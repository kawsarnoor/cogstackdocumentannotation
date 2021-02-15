<template>
<!-- eslint-disable -->
    <div class="container" id="progress">
        <!-- <img alt="Vue logo" src="../assets/uclh.png" style="max-width: 60%"> -->
        <div class="card text-center" style="display: inline-block;">
            <div class="card-header">
                <div class="column is-two-thirds">Finished {{ completed_ids.length}} of {{ document_ids.length}} </div>
                <span class="column" @click="goToCurrentIndexPage()"><a><i class="fa fa-bookmark fa-1x"></i></a></span>
            </div>
            <div class="list-group list-group-flush">
                <template v-for="(docindx, idx) in viewable_documents">
                    <div class="btn-group" :key="docindx" role="group" aria-label="Basic example">
                        <div class="input-group-prepend">
                            <div class="input-group-text" id="btnGroupAddon">{{ docindx }}</div>
                        </div>
                        <button v-if="docindx==currentidx" :key="docindx"  type="button" class="list-group-item list-group-item-action active" @click="goToDocument(docindx)"><span v-if="completed_ids.includes(docindx)"  style='font-size:15px;'>&#10004;</span> Doc {{ docindx }}</button>
                        <button v-else type="button" :key="docindx"  class="list-group-item list-group-item-action" @click="goToDocument(docindx)"><span v-if="completed_ids.includes(docindx)"  style='font-size:15px;'>&#10004;</span> Doc {{ docindx }}</button>
                    </div>
                </template>
            </div>
        </div>
        <div>
            <button class="btn btn-primary" type="button" style="margin-right: 15px; margin-top: 10px;" @click="previousPage()">Prev</button>
            <button class="btn btn-primary" type="button" style="margin-left: 15px; margin-top: 10px;" @click="nextPage()">Next</button>
        </div>
    </div>
</template>

<script>
/*eslint-disable*/
import axios from 'axios';
import { EventBus } from "../main.js";

export default {
  name: 'Progess',
  props: {
    numbers: Number,
    projectid: Number,
  },

  data() {
      return {
        projectid: Number,
        nlptasktype: '',
        currentidx: Number,
        document_ids: [],
        completed_ids: [],
        viewable_documents: [],
        documents_per_page: Number,
        pageNumber: Number,
        root_api: process.env.VUE_APP_URL,
      };
  },
  methods: {

    nextPage() {
           console.log('getting next page')

           this.pageNumber = this.pageNumber + 1
           var top_doc = (this.pageNumber) * this.documents_per_page;
           var bottom_doc = top_doc + this.documents_per_page;
           
           if(this.document_ids.length > top_doc - 1) {
                this.viewable_documents = this.document_ids.slice(top_doc, bottom_doc)

        //    if (this.document_ids.includes(top_doc+1)) {
        //         this.viewable_documents = this.document_ids.slice(top_doc, bottom_doc)
           } else {
               this.pageNumber = this.pageNumber - 1 // stay on the same page
           }
    },
    
    previousPage() {

        console.log('getting previous page')
        if (this.pageNumber < 1) {
            return;
        }
        this.pageNumber = this.pageNumber - 1
        var top_doc = (this.pageNumber) * this.documents_per_page
        var bottom_doc = top_doc + this.documents_per_page
        this.viewable_documents = this.document_ids.slice(top_doc, bottom_doc)

    },

    goToCurrentIndexPage() {

        var lastDocument = Math.max(...this.completed_ids)
        var pos = (this.document_ids).indexOf(lastDocument)
        
        this.pageNumber = Math.floor(pos/this.documents_per_page);
        var top_doc = (this.pageNumber) * this.documents_per_page
        var bottom_doc = top_doc + this.documents_per_page

        this.currentidx = lastDocument
        this.viewable_documents = this.document_ids.slice(top_doc, bottom_doc)
    },

    next() {
            if (this.currentidx <  this.document_ids[this.document_ids.length - 1] ) {
                this.currentidx = this.currentidx + 1;
                console.log('going forward to document ', this.currentidx);
                EventBus.$emit("number-added", this.currentidx); 

                if (this.currentidx > Math.max(...this.viewable_documents)){
                    this.nextPage()
                }

            }
            else {
                console.log('End of dataset');
            }
    },

    prev() {
            if (this.currentidx > this.document_ids[0]) {
                this.currentidx = this.currentidx - 1;
                console.log('going back to document ', this.currentidx);
                EventBus.$emit("number-added", this.currentidx); 

                if (this.currentidx < Math.min(...this.viewable_documents)){
                    this.previousPage()
                }
            }
            else {
                console.log('Start of dataset');
            }
    },

    goToDocument(i) {
        this.currentidx = i;
        EventBus.$emit("number-added", i);
    }

  },

  created() {
    
    // Refresh page at start of component creation. Is there a more Vue-ish way of doing this?
    if (localStorage.getItem('forceRefresh') === 'refresh') {
        localStorage.setItem('forceRefresh', '');
        window.location.reload();
    }

    this.currentidx = 1; // retrieve using api
    this.pageNumber = -1;
    this.documents_per_page = 10

    console.log('Progresss loaded with cid: ', this.currentidx);

    const path = 'http://' + this.root_api + ':5001/getCompleted';
    axios.post(path, {'project_id': this.projectid}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
            this.document_ids = res.data.document_ids;
            this.completed_ids = res.data.completed_ids;
            this.nlptasktype = res.data.nlptasktype;
            this.currentidx = this.document_ids[0];

            // load in first x documents
            this.nextPage();
        })
        .catch((error) => {
            console.error(error);
    });

    // Event listener for previous and next document
    window.addEventListener('keydown', (e) => {
      if (e.key == 'ArrowLeft') {
        this.prev();
      }
      if (e.key == 'ArrowRight') {
        this.next();
      }
    });

    EventBus.$on("label-added", idx => {
      console.log('label-added: ',idx);
      if (!this.completed_ids.includes(idx)) {
            const path = 'http://' + this.root_api + ':5001/getCompleted';
            axios.post(path, {'project_id': this.projectid}, {headers: {'Authorization': localStorage.getItem('jwt')}})
            .then((res) => {
                this.document_ids = res.data.document_ids;
                this.completed_ids = res.data.completed_ids;
            })
            .catch((error) => {
                console.error(error);
            });
      }
      // This is the code that we use to automatically move to next document. Useful only for multiclass
      if (this.nlptasktype == 'multiclass'){
        this.next();
      }
    });

  }

  
};
</script>

<style scoped>

#progress{
    background-color: white;
    padding: 0px 0px;
}
.overflowAuto {
  overflow-x: hidden;
  overflow-y: auto;
  height: calc(100vh - 600px);
}

.list-group{
    max-height: 500px;
    margin-bottom: 10px;
    overflow:scroll;
    -webkit-overflow-scrolling: touch;
}


</style>
