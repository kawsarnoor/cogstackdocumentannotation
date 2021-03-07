<template>
<!-- eslint-disable-->
  <div class="columns">
    <div class="column is-two-thirds">
        <div class="card text-center">
          <div class="card-body" id='document_text'>
            <p class="card-text overflowAuto">
              <span v-for="(span, span_idx) in document_tokens" :key="span" >
                <span :id="'span_' + span_idx" v-if="span.nlp_cuis != ''" class="tag is-info is-medium">
                    <span @click="displayEntity(span, span_idx)" class="chosen">{{ document_text.slice(span['start'],span['end'])}}</span>
                    <button class="delete is-small" @click="deleteEntity(span, span_idx)"></button>
                </span>
                <span :id="'span_' + span_idx" v-else>
                  {{ document_text.slice(span['start'],span['end']) }}
                </span>
              </span>
            </p>
          </div>
      </div>
    </div>
    <div class="column">
         <div class="card has-text-left">
          <div class="card-body" id='document_text'>
            <div class="card-text">

              <article class="message is-info">
                <div class="message-header">
                  <p>Entity Information</p>
                </div>
                <div class="message-body">

                  <div class="dropdown" id='searchcontainer'>
                    <div class="dropdown ">
                      <div class="dropdown-trigger">
                          <div class="field">
                              <p class="control is-expanded has-icons-right">
                                  <input class="input is-rounded" type="text" placeholder="Search for alternative concept" @keyup.enter="searchConcept()" v-model.lazy="searchConceptString">
                                  <span class="icon is-small is-right"><i class="fa fa-search"></i></span>
                              </p>
                          </div>
                      </div>
                      <div class="dropdown-menu" role="menu" >
                        <div class="dropdown-content" v-for="result in searchresults">
                          <a class="dropdown-item" @click="changelabel(result._source.cui)">
                            <p><strong>CUI</strong>: {{ result._source.cui }} <strong>Pretty Name</strong>: {{ result._source.pretty_name }}</p>
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>

                  <p><strong>CUI: </strong> {{ current_entity_label_info.cui }}</p>
                  <p><strong>Pretty Name: </strong>{{ current_entity_label_info.pretty_name }}</p>
                  <p><strong>Source Text: </strong> {{ current_entity_label_info.source_text }}</p>
                  <p><strong>TUI: </strong>{{ current_entity_label_info.tui }}</p>
                  <p><strong>Type: </strong>{{ current_entity_label_info.type }}</p>
                </div>
              </article>

              <article class="message is-info">
                <div class="message-header">
                  <p>Meta Information</p>
                </div>
                <div class="message-body">
              <h5>Negated</h5>
                  <button class="button is-rounded is-success"> <span class="icon"><i class="fa fa-check"></i></span> <span>Negated</span></button>
                  <h5>Experienced</h5>
                  <button class="button is-rounded"> <span>Patient</span></button>
                  <button class="button is-rounded is-success"> <span class="icon"><i class="fa fa-check"></i></span> <span>Non-Patient</span></button>
                </div>
              </article>
            
            </div>
          </div>
      </div>
    </div>
  </div>
</template>

<script>
/*eslint-disable*/

import axios from 'axios';
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
      document_tokens: [],
      labels: [],
      searchresults: [],
      spans: {},
      spanvalues: [],
      currentidx: Number, // this is current document_idx
      root_api: process.env.VUE_APP_URL,
      current_entity_label_info: [],
      current_span: '',
      searchConceptString: '',
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
      const path = 'http://' + this.root_api + ':5001/getDocumentNER';
      axios.post(path, {'document_id': newIdx ,'project_id': this.projectid}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.document_text = res.data.document_text;
          this.document_tokens = res.data.document_tokens;
          let searchContainer = document.getElementById("searchcontainer");
          searchContainer.classList.remove('is-active')
        })
        .catch((error) => {
          console.error(error);
        });
    },

    changelabel(label_id) {
      const path = 'http://' + this.root_api + ':5001/changelabel';
      let current_entity = this.document_tokens[this.current_entity_label_info.span_idx]
      axios.post(path, { 'label_id': label_id, 'current_entity': current_entity, 'document_id': this.currentidx, 'project_id': this.projectid},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.getnextdocument(this.currentidx)
        })
        .catch((error) => {
          console.error(error);
        });
    },

    displayEntity(span, span_idx){
      this.current_entity_label = span.nlp_cuis
      console.log(span)
      const path = 'http://' + this.root_api + ':5001/getEntityInfo';

      axios.post(path, { 'cui': span.nlp_cuis, 'unique': true},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.current_entity_label_info = res.data.entity_information
          this.current_entity_label_info['source_text'] = this.document_text.slice(span['start'],span['end'])
          this.current_entity_label_info['span_idx'] = span_idx
        })
        .catch((error) => {
          console.error(error);
        });
    },

    deleteEntity(span, span_idx){

      document.getElementById("span_" + span_idx).classList.remove('is-info');

      const path = 'http://' + this.root_api + ':5001/deleteEntity';

      axios.post(path, { 'entity': span, 'project_id': this.projectid, 'document_id': this.currentidx},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          this.getnextdocument(this.currentidx)
        })
        .catch((error) => {
          console.error(error);
        });
    },

    searchConcept(){
      if (this.searchConceptString === ""){
        let searchContainer = document.getElementById("searchcontainer");
        searchContainer.classList.remove('is-active')
        return
      }

      const path = 'http://' + this.root_api +':5001/searchconceptinelastic';

      axios.post(path, {'searchConceptString': this.searchConceptString, 'unique': false},
                        {headers: {'Authorization': localStorage.getItem('jwt')}})
      .then((res) => {
          this.searchresults = res.data.searchresult
          let searchContainer = document.getElementById("searchcontainer");
          searchContainer.classList.add('is-active')
      })
      .catch((error) => {
          console.error(error);
      });

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
span.chosen:hover {
  text-decoration: none;
  cursor: pointer;
}

.dropdown {
  width: 100%;
}
.dropdown-trigger {
    width: 100%
}


</style>
