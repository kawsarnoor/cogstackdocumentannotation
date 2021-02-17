<template>
    <nav class="navbar is-mobile is-primary text-center">
      <div class="navbar-brand">
        <a class="navbar-item" @click="home()">
          <img src="https://avatars.githubusercontent.com/u/28688163?s=280&v=4" width="28" height="28">
        </a>
      </div>
      <div class="navbar-end">
        <button class="btn btn-primary" type="button" @click="logout()">
          {{ username }}
          <i class="fa fa-sign-out"></i>
        </button>
      </div>
    </nav>
</template>

<script>
/*eslint-disable*/

	import { mapGetters } from 'vuex'
  import axios from 'axios';
  import router from '../router'
  
	export default {
        
    data() {
      return {
        username: localStorage.getItem('user'),
        isAdmin: localStorage.getItem('isAdmin'),
      };
    },

		computed: {
			...mapGetters('auth', {
				isAuth: 'isAuthenticated',
			})
    },
        
    methods: {
      logout: function () {
        this.$store.dispatch('auth/logout');
      },

      home: function () {
        router.push('/projects');
      },
      
    },
	}
</script>

<style>
a {
  color: white;
  font-size: 35px;
  text-decoration: none;
}

nav {
  padding-bottom: 20px;
}

img {
  height: 75px;
  margin: 10px;
}
</style>