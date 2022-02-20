<template>
<!-- eslint-disable max-len -->
  <div class="document">
    <div class="card text-center">
      <div class="card-header">
        <div class="category">
          <div class="row">
            <div class="col-12">
              <div class="btn-group" role="group" v-for="(label, idx) in available_labels" :key="label">
                    <div v-if="labels.includes(available_label_ids[idx])" class="buttons has-addons">
                      <button class="button is-success" @click="changelabel(available_label_ids[idx])">{{label}}</button>
                      <button class="button" @click="linkTexttoLabel(available_label_ids[idx])">
                        <i class="fa fa-quote-right"></i>
                      </button>
                      <button class="button" @click="highlightspans(available_label_ids[idx])">
                        <i class="fa fa-eye"></i>
                      </button>
                    </div>
                    <button v-else class="button" @click="changelabel(available_label_ids[idx])"> {{label}} </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="card-body" id='document_text'>
        <p class="card-text overflowAuto has-text-left">
          <span v-for="(span, span_idx) in document_text['tokens']" :key="span" >
              <span v-html="document_text['text'].slice(span['start'],span['end'])" :id="'span_' + span_idx" />{{ ' ' }}
          </span>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
/*eslint-disable*/

import axios from 'axios';
import rangy from 'rangy';
import { EventBus } from "../main.js";
import $ from 'jquery';


export default {
  name: 'MultiLabelDocument',
  props: {
    msg: String,
    projectid: Number,
  },

  data() {
    return {
      available_labels: [],
      available_label_ids: [],
      document_text: '',
      labels: [],
      linkedspans: [],
      currentidx: Number, // this is current document_idx
      root_api: process.env.VUE_APP_URL,
    };
  },
  methods: {
    
    retrieveAnnotatedDocument(idx) {
      const ann_document_pathpath = 'http://' + this.root_api + ':5001/getAnnotatedDocumentMultiClassMultiLabel';
      axios.post(ann_document_pathpath, {'document_id': idx}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.labels = res.data.label_ids;
          console.log('retrieve annotated document', idx)
        })
        .catch((error) => {
          console.error(error);
        });   
    },

    loadProject() {
      const path = 'http://' + this.root_api + ':5001/getProject';
      axios.post(path, {'project_id': this.projectid}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.available_labels = res.data.available_labels;
          this.available_label_ids = res.data.available_label_ids;
          console.log('loaded available labels')
          var starting_document_id = res.data.starting_document_id;
          this.getnextdocument(starting_document_id); // this needs to be logged to dataset and not document

        })
        .catch((error) => {
          console.error(error);
        });      
    },

    getnextdocument(newIdx) {
      const document_path = 'http://' + this.root_api + ':5001/getDocument';
      axios.post(document_path, {'document_id': newIdx}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.document_text = res.data.document_tokens;
          // this.document_text = this.document_text.replace(new RegExp('\r?\n','g'), '<br/>');
          this.retrieveAnnotatedDocument(newIdx);

          // Highlight all of the linked spans of texts
          for (let i=0; i<this.available_label_ids.length; i++){
            this.getlinkedspans(this.available_label_ids[i]); 
          }
          
        })
        .catch((error) => {
          console.error(error);
        });

    },

    changelabel(label_id) {
      const path = 'http://' + this.root_api + ':5001/changelabel';
      axios.post(path, { 'label_id': label_id, 'document_id': this.currentidx, 'project_id': this.projectid},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          EventBus.$emit("label-added", this.currentidx);
          this.retrieveAnnotatedDocument(this.currentidx)
        })
        .catch((error) => {
          console.error(error);
        });
    },

    linkTexttoLabel(label_id) {
      const sel = rangy.getSelection();
      const span_ids = [];

      if ((sel == '') || (sel.rangeCount == 0)){
        return
      }

      for (let r = 0, range, spans; r < sel.rangeCount; ++r) {
          range = sel.getRangeAt(r);
          // If a single span (word phrase) is chosen do the following
          if (range.startContainer == range.endContainer && range.startContainer.nodeType == 3) {
              range = range.cloneRange();
              range.selectNode(range.startContainer.parentNode);
          }
          spans = range.getNodes([1], function(node) {
              return node.nodeName.toLowerCase() == "span";
          });
          for (let i = 0, len = spans.length; i < len; ++i) {
            if (spans[i].id){
              span_ids.push(spans[i].id);
            }  
          }
      }
      
      const path = 'http://' + this.root_api + ':5001/addSpanToAnnotation';
      axios.post(path, {'document_id': this.currentidx, 'project_id': this.projectid, 'label_id': label_id, 'span_ids': span_ids},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then(() => {
          console.log('label added succesfully')
          this.getlinkedspans(label_id);
        })
        .catch((error) => {
          console.error(error);
      });
    },

    getlinkedspans(label_id) {
      const path = 'http://' + this.root_api + ':5001/getSpansForAnnotation';
      axios.post(path, {'document_id': this.currentidx, 'project_id': this.projectid, 'label_id': label_id},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          console.log('spans retrieved succesfully')
          
          for (let i=0; i < res.data.snippets.length; i++){
            var snippets = (res.data.snippets)[i].split(',')
            for (let j=0; j < snippets.length; j++){
              $('#span_'+snippets[j]).css('background-color',"#00FFFF")
              $('#span_'+snippets[j]).parent().css( "background-color", "#00FFFF" )
            }
          }

        })
        .catch((error) => {
          console.error(error);
      });
    },

    highlightspans(label_id) {
      const path = 'http://' + this.root_api + ':5001/getSpansForAnnotation';
      axios.post(path, {'document_id': this.currentidx, 'project_id': this.projectid, 'label_id': label_id},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          console.log('spans retrieved succesfully')
          
          for (let i=0; i < res.data.snippets.length; i++){
            var snippets = (res.data.snippets)[i].split(',')
            for (let j=0; j < snippets.length; j++){
              $('#span_'+snippets[j]).css('background-color',"#FFFF00")
            }
          }

          this.sleep(1000).then(function() {
            console.log('done sleeping')
            for (let i=0; i < res.data.snippets.length; i++){
              var snippets = (res.data.snippets)[i].split(',')
              for (let j=0; j < snippets.length; j++){
                $('#span_'+snippets[j]).css('background-color',"#00FFFF")
              }
            }
          })
          
        })
        .catch((error) => {
          console.error(error);
      });
    },

    sleep(ms) {
      console.log('sleeping for some time now')
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  
  },

  created() {
    this.currentidx = 1; // risky..the starting coder might not be set up
    console.log('Document loaded with cid: ', this.currentidx);

    this.loadProject(this.project_id); // this gives us the available labels

    EventBus.$on("number-added", newIdx => {
      console.log('number added called')
      this.currentidx = newIdx;
      this.getnextdocument(newIdx);
      
    });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
input {
  margin: 3px;
}
h3 {
  margin: 0px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.category {
  text-align: left;
  margin-top: 15px;
}
.overflowAuto {
  overflow-y: auto;
  height: 75vh;
  word-wrap: break-word;
}
.document {
  margin: 15px;
}
.btn-group {
  margin: 5px;
}
div.boxwrap div {
  float: left;
}
div.boxwrap div:hover {
  background-color: aqua;
  cursor: pointer;
}
div.boxwrap div h5 {
  text-align: center;
}
pre {
  white-space: pre-wrap;
  word-break: keep-all
}
</style>
