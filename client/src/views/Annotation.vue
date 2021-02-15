<template>
  <div class="home">
    <div class="row home-row" >
      <div class="col-sm-2" id='progress'>
        <Header/>
        <Progress  :numbers="numbers" :projectid="projectid" @number-added="numbers = $event"/>
      </div>
      <div class="col-sm-10">
        <Document msg="Medical Text Classification Annotation Tool" :projectid="projectid"/>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import Progress from '@/components/Progress.vue';
import Document from '@/components/Document.vue';
import Header from '@/components/Header.vue';


export default {
  name: 'Annotation',
  components: {
    Header,
    Progress,
    Document,
  },
  data() {
    return {
      numbers: 0,
      projectid: Number,
    };
  },
  created() {
    this.projectid = this.$route.params.projectid;
    console.log('annotation page: ', this.projectid);
  },
};
</script>

<style scoped>
.home {
  margin: 30px 0px 0px 0px;
}

.home-row {
  height: 80%;
}

#progress{
  height: 80%;
}

</style>
