<template>
<!-- eslint-disable max-len -->
  <div>
    <Header/>
    <div class="row home-row" >
      <div class="col-sm-2" id='progress'>
        <Progress :numbers="numbers" :projectid="projectid" @number-added="numbers = $event"/>
      </div>
      <div class="col-sm-10">
        <MultiLabelDocument  v-if="nlptasktype == 'multilabel'" msg="Medical Text Classification Annotation Tool" :projectid="projectid"/>
        <MultiClassDocument v-if="nlptasktype == 'multiclass'" msg="Medical Text Classification Annotation Tool" :projectid="projectid"/>
      </div>
    </div>
  </div>
</template>

<script>
/*eslint-disable*/

// @ is an alias to /src
import axios from 'axios';
import Progress from '@/components/Progress.vue';
import MultiLabelDocument from '@/components/MultiLabelDocument.vue';
import MultiClassDocument from '@/components/MultiClassDocument.vue';

import Header from '@/components/Header.vue';


export default {
  name: 'Annotation',
  components: {
    Header,
    Progress,
    MultiLabelDocument,
    MultiClassDocument,
  },
  data() {
    return {
      numbers: 0,
      projectid: Number,
      nlptasktype: '',
      root_api: process.env.VUE_APP_URL,
    };
  },

  methods: {

    loadProjectDetails() {
      const path = 'http://' + this.root_api + ':5001/getProject';
      axios.post(path, {'project_id': this.projectid}, {headers: {'Authorization': localStorage.getItem('jwt')}})
        .then((res) => {
          console.log('loaded available labels')
          this.nlptasktype = res.data.nlptasktype;
        })
        .catch((error) => {
          console.error(error);
        });      
    },

  },

  created() {
    this.projectid = this.$route.params.projectid;
    console.log('annotation page: ', this.projectid);
    this.loadProjectDetails();
  },
};
</script>

<style scoped>
.home {
  margin: 30px 0px 0px 0px;
}

.home-row {
  height: 80%;
  margin: 30px 0px 0px 0px;
}

#progress{
  height: 80%;
}

</style>
