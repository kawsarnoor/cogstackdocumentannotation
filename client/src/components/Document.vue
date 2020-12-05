<template>
<!-- eslint-disable max-len -->
  <div class="document">
    <div class="card text-center">
      <div class="card-header">
        <div class="category">
          <div class="row">
            <div class="col-12">
              <div class="btn-group" role="group" v-for="(label, idx) in available_labels" :key="label">
                    <!-- <button v-if="value == false" class="btn btn-secondary" type="button" @click="changeValue(label, 'themes', labels.id)">{{label}} </button>
                    <button v-if="value == true" class="btn btn-primary" type="button" @click="showSpans(label, 'themes', labels.id)">{{label}} </button>
                    <button v-if="value == true" class="btn btn-warning" type="button" @click="changeValue(label, 'themes', labels.id)">&#10008;</button>
                    <button v-if="value == true" class="btn btn-warning" type="button" @click="linkTexttoLabel(label, 'themes', labels.id)">&#10078;</button> -->
                    <button v-if="labels.includes(available_label_ids[idx])" class="btn btn-primary" type="button" @click="changelabel(available_label_ids[idx])"> {{label}} </button>
                    <button v-else class="btn btn-secondary" type="button" @click="changelabel(available_label_ids[idx])"> {{label}} </button>
              </div>
            </div>
            <!-- <div class="col-2">
              <form class="form-inline">
                <input type="text" id="themes-new" class="form-control search" placeholder="new label" @keyup.enter="addlabel('themes-new')">
              </form>
            </div> -->
          </div>
        </div>
      </div>
      <div class="card-body" id='document_text'>
        <p class="card-text overflowAuto">
          <pre>{{document_text}}</pre>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
/*eslint-disable*/

import axios from 'axios';
import rangy from 'rangy';
import $ from 'jquery';
import { EventBus } from "../main.js";

export default {
  name: 'Document',
  props: {
    msg: String,
  },
  data() {
    return {
      project_id: Number,
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

    loadProject(project_id) {
      const path = 'http://' + this.root_api + ':5001/getProject';
      axios.post(path, {'project_id': project_id}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.available_labels = res.data.available_labels;
          this.available_label_ids = res.data.available_label_ids;
          console.log('loaded available labels')
        })
        .catch((error) => {
          console.error(error);
        });      
    },

    getnextdocument(newIdx) {
      const document_path = 'http://' + this.root_api + ':5001/getDocument';
      axios.post(document_path, {'document_id': newIdx}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.document_text = res.data.document_text;
          // this.document_text = this.document_text.replace(new RegExp('\r?\n','g'), '<br/>');
          this.retrieveAnnotatedDocument(newIdx);
        })
        .catch((error) => {
          console.error(error);
        });

    },

    changelabel(label_id) {
      const path = 'http://' + this.root_api + ':5001/changelabel';

      axios.post(path, { 'label_id': label_id, 'document_id': this.currentidx, 'project_id': this.project_id},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          EventBus.$emit("label-added", this.currentidx);
        })
        .catch((error) => {
          console.error(error);
        });
    },

  },

  created() {
    this.project_id = 1; // replace this with a call to the api!
    this.currentidx = 1; // risky..the starting coder might not be set up
    console.log('Document loaded with cid: ', this.currentidx);

    this.loadProject(this.project_id); // this gives us the available labels
    this.getnextdocument(1);

    // Event listener for previous and next document
    window.addEventListener('keydown', (e) => {
      if (e.key == 'y') {
        this.changelabel(2);
      }
      if (e.key == 'n') {
        this.changelabel(1);
      }
    });

    EventBus.$on("number-added", newIdx => {
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
