<template>
    <nav class="navbar navbar-light bg-light text-center">
      <a v-if="isAuth">
        <button class="btn btn-primary" type="button" @click="home()" style="margin:10px">
          <i class="fa fa-home"></i>
        </button>
        <button class="btn btn-primary" type="button" @click="logout()">
          {{ username }}
          <i class="fa fa-sign-out"></i>
        </button>
      </a>
      <a v-else>
        <button class="btn btn-primary" type="button" @click="logout()">
          do not annotate!
        </button>
      </a>
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
            }
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