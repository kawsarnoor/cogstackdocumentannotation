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

                      <button class="button" @click="linkTexttoLabel(label, idx)">
                        <i class="fa fa-quote-right"></i>
                      </button>
                      <button class="button">
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
        <p class="card-text overflowAuto">
          <span v-for="(span, span_idx) in document_text['tokens']" :key="span" :id="'span_' + span_idx">
            {{ document_text['text'].slice(span['start'],span['end'])}}
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

export default {
  name: 'NERDocument',
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
      spans: {},
      spanvalues: [],
      currentidx: Number, // this is current document_idx
      root_api: process.env.VUE_APP_URL,
    };
  },
  methods: {
    
    retrieveAnnotatedDocument(idx) {
      const ann_document_pathpath = 'http://' + this.root_api + ':5001/getAnnotatedDocument';
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

    linkTexttoLabel(label, label_id) {
      const sel = rangy.getSelection();
      const span_ids = [];
      for (let r = 0, range, spans; r < sel.rangeCount; ++r) {
          range = sel.getRangeAt(r);
          // If a single span (word phrase) is chosen do the following
          if (range.startContainer == range.endContainer && range.startContainer.nodeType == 3) {
              if (sel == ''){
                break // This is a hack. Clicking on part of the screen is registered to one of the spans
              }
              range = range.cloneRange();
              range.selectNode(range.startContainer.parentNode);
          }
          spans = range.getNodes([1], function(node) {
              return node.nodeName.toLowerCase() == "span";
          });
          for (let i = 0, len = spans.length; i < len; ++i) {
              span_ids.push(spans[i].id);
          }
      }
      
      // this.spans[category][label] = this.spans[category][label].concat(ids);
      // const path = 'http://' + this.root_api + ':5001/updateSpans';
      // let newspans = this.spans[category][label];
      
      // axios.post(path, {category, label, newspans, id })
      //   .then(() => {
      //     this.getnextdocument(this.currentidx);
      //   })
      //   .catch((error) => {
      //     console.error(error);
      // });
    },
  

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
