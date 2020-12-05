<template>
  <div class="home">
    <div class="row home-row" >
      <div class="col-sm-2" id='progress'>
        <Header/>
        <Progress  :numbers="numbers" @number-added="numbers = $event"/>
      </div>
      <div class="col-sm-10">
        <Document msg="Medical Text Classification Annotation Tool"/>
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
    };
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
