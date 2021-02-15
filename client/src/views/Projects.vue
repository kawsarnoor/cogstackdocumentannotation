<template>
<!-- eslint-disable  -->
<div>
    <Header/>

<div class="section">
    
  <div class="container is-fluid">
    <h1 class="title is-2">
      Projects
    </h1>
    <h3 class="subtitle is-4">
      <!-- Visible -->
    </h3>
    <div class="cards">
      <div class="card" v-for="(project, idx) in projects" :key="project">
        <div class="card-content">
          <p class="title">
            {{ project.name }}
          </p>
          <p class="subtitle">
            {{ project.description }}
          </p>
        </div>
        <footer class="card-footer">
          <p class="card-footer-item">
            <button class="btn btn-primary" type="button" @click="openProject(project.id)"> Open </button>
          </p>
        </footer>        
      </div>
    </div>
  </div>
</div>
</div>


</template>

<script>
/*eslint-disable*/
import Header from '@/components/Header.vue';
import axios from 'axios';
import router from '../router'

export default {

  name: 'Projects',
  components: {
    Header,
  },
  data() {
    return {
      projects: [],
      root_api: process.env.VUE_APP_URL,
    };
  },

  methods: {
  
      retrieveProjects() {
        var user = localStorage.getItem('user');
        const path = 'http://' + this.root_api + ':5001/getProjects';

        axios.post(path, {}, {headers: {'Authorization': localStorage.getItem('jwt')}})
          .then((res) => {
            this.projects = res.data.projects;
            console.log('retrieve projects')
          })
          .catch((error) => {
            console.error(error);
          });   
      },

      openProject(project_id) {
        console.log(project_id)
        router.push({ name: 'Annotation', params: {projectid: project_id}});
      }
  },

  created() {
    this.retrieveProjects();
  },
};

</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, 20rem);
  grid-gap: 1.5rem;
  justify-content: space-between;
  align-content: flex-start;
}

</style>
