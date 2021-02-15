/* eslint-disable */ 
import Vue from 'vue';
import Router from 'vue-router';
import Login from './views/Login.vue';
import Annotation from './views/Annotation.vue';
import Projects from './views/Projects.vue'

Vue.use(Router);

let router = new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
      {
        path: '/login',
        alias: '/',
        name: 'Login',
        component: Login,
        meta: {
            requiresAuth: false,
            forceRefresh: true
        }
      },
      {
        path: '/projects',
        name: 'Projects',
        component: Projects,
        meta: {
            requiresAuth: true,
            forceRefresh: true
        }
      },
      {
        path: '/annotation/:projectid',
        name: 'Annotation',
        component: Annotation,
        meta: {
            requiresAuth: true,
            forceRefresh: false
        }
      },
    ],
  });

  router.beforeEach((to , from, next) => {
    console.log('checking route')
    if (to.matched.some(route => route.meta.forceRefresh)) {
        localStorage.setItem('forceRefresh', 'refresh')
    }

    if (to.matched.some(route => route.meta.requiresAuth)) {
        if (localStorage.getItem('jwt') == null || localStorage.getItem('jwt') == 'undefined' || localStorage.getItem('jwt') == ''){
            next({
                name:'Login',
		params: { nextUrl: to.fullPath}
	    })
	} else{
            next()
	}
    } else{
        console.log('rejected going to login');
	next()
    }
})

export default router;
