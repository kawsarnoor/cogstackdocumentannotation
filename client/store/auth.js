/*eslint-disable*/

import axios from 'axios';
import router from '../src/router'

const root_api = process.env.VUE_APP_URL

const state = {
    // single source of data
    user: {},
	jwt: '',
	forceRefresh: '',
};

const actions = {
    login: ({commit}, loginDetails) => {
        var username = loginDetails['username']
        var password = loginDetails['password'] 
		console.log(root_api);
        const path = 'http://' + root_api +  ':5001/login';

        return new Promise((resolve, reject) => {
			axios.post(path, {'username':username, 'password':password})
				.then(res => {
				commit('authUser', { user: username, jwt: res.data.token });	
				console.log('succesfully logged in...');

				localStorage.setItem('jwt', res.data.token);
				localStorage.setItem('isAdmin', res.data.isAdmin);
				localStorage.setItem('user', username);
				localStorage.setItem('forceRefresh', 'refresh');

				resolve({'result': 'success'})

			})
			.catch((error) => {
				console.log('failed log in...');
				console.log(error);
				reject(error);
            });  
        })
 
	},
	
	refreshtoken: ({commit}) => {
		let token = localStorage.getItem('jwt');
		const path = 'http://' + root_api + ':5001/refreshtoken';
		
        axios.post(path, {'user': localStorage.getItem('user')}, {headers: {'Authorization': localStorage.getItem('jwt')}})
            .then(res => {
			  commit('authUser', { user: localStorage.getItem('user'), jwt: res.data.token });	
              console.log('succesfully refreshed token...');

			  localStorage.setItem('jwt', res.data.token);
			  localStorage.setItem('user', localStorage.getItem('user'));
            })
            .catch((error) => {
			//    router.push('/login'); 
            });
	},

	logout: ({commit}) => {
		commit('clearAuthData');
		localStorage.removeItem('user');
		localStorage.removeItem('jwt');
		localStorage.setItem('forceRefresh', '');
		router.replace('login');
	},
};

const mutations = {
	authUser(state, userData) {
		state.user = userData.username;
		state.jwt = userData.token;
		state.forceRefresh = false;
	},
	clearAuthData(state) {
		state.user = {};
		state.jwt = '';
		state.forceRefresh = true;
	},
};

const getters = {
    // reusable data accessors
    isAuthenticated (state) {
	  if (localStorage.getItem('jwt')){
          return true;
	  } else {
		  return false;
	  }
    //   return isValidJwt(state.jwt.token)
    }
};

export default {
	namespaced: true,
	state,
	mutations,
	getters,
	actions,
}

