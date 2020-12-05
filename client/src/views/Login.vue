<template>
<!-- eslint-disable max-len -->
<div class="column is-4 is-offset-4">
  <div class="box">
        <h2>Login</h2>
        <div v-if="login_failed" class="notification is-danger">
        Incorrect username or password
        </div>
        <form>
          <div class="form-group">
            <input type="text" class="form-control" id="username" placeholder="username">
            <input type="password" class="form-control" id="password" placeholder="password">
          </div>
          <div>
            <a target="_blank"><button class="btn btn-primary" type="button" @click="authenticateLoginDetails()">login</button></a>
          </div>
        </form>
  </div>
</div>
</template>

<script>
/*eslint-disable*/

import axios from 'axios';
import $ from 'jquery';
import router from '../router'

export default {

  name: 'Login',
  data() {
    return {
      msg: 'Hi!',
      esindices: [],
      login_failed: false,
    };
  },

  methods: {
        authenticateLoginDetails() {
          var username = $("#username")[0].value;
          var password = $("#password")[0].value;

          var logindetails = {'username': username, 'password': password};

          this.$store.dispatch('auth/login', logindetails).then(response => {
              console.log("Got some data, now lets show something in this component")
              router.push('/projects');
          }, error => {
              console.log("Got nothing from server. Prompt user to check internet connection and try again")
              this.login_failed = true
          })
        }

  },

  created() {
    
  },
};

</script>
