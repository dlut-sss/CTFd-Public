/******/ (function(modules) { // webpackBootstrap
/******/ 	// install a JSONP callback for chunk loading
/******/ 	function webpackJsonpCallback(data) {
/******/ 		var chunkIds = data[0];
/******/ 		var moreModules = data[1];
/******/ 		var executeModules = data[2];
/******/
/******/ 		// add "moreModules" to the modules object,
/******/ 		// then flag all "chunkIds" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0, resolves = [];
/******/ 		for(;i < chunkIds.length; i++) {
/******/ 			chunkId = chunkIds[i];
/******/ 			if(installedChunks[chunkId]) {
/******/ 				resolves.push(installedChunks[chunkId][0]);
/******/ 			}
/******/ 			installedChunks[chunkId] = 0;
/******/ 		}
/******/ 		for(moduleId in moreModules) {
/******/ 			if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
/******/ 				modules[moduleId] = moreModules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(parentJsonpFunction) parentJsonpFunction(data);
/******/
/******/ 		while(resolves.length) {
/******/ 			resolves.shift()();
/******/ 		}
/******/
/******/ 		// add entry modules from loaded chunk to deferred list
/******/ 		deferredModules.push.apply(deferredModules, executeModules || []);
/******/
/******/ 		// run deferred modules when all chunks ready
/******/ 		return checkDeferredModules();
/******/ 	};
/******/ 	function checkDeferredModules() {
/******/ 		var result;
/******/ 		for(var i = 0; i < deferredModules.length; i++) {
/******/ 			var deferredModule = deferredModules[i];
/******/ 			var fulfilled = true;
/******/ 			for(var j = 1; j < deferredModule.length; j++) {
/******/ 				var depId = deferredModule[j];
/******/ 				if(installedChunks[depId] !== 0) fulfilled = false;
/******/ 			}
/******/ 			if(fulfilled) {
/******/ 				deferredModules.splice(i--, 1);
/******/ 				result = __webpack_require__(__webpack_require__.s = deferredModule[0]);
/******/ 			}
/******/ 		}
/******/ 		return result;
/******/ 	}
/******/
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// object to store loaded and loading chunks
/******/ 	// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 	// Promise = chunk loading, 0 = chunk loaded
/******/ 	var installedChunks = {
/******/ 		"pages/notifications": 0
/******/ 	};
/******/
/******/ 	var deferredModules = [];
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "/themes/admin/static/js";
/******/
/******/ 	var jsonpArray = window["webpackJsonp"] = window["webpackJsonp"] || [];
/******/ 	var oldJsonpFunction = jsonpArray.push.bind(jsonpArray);
/******/ 	jsonpArray.push = webpackJsonpCallback;
/******/ 	jsonpArray = jsonpArray.slice();
/******/ 	for(var i = 0; i < jsonpArray.length; i++) webpackJsonpCallback(jsonpArray[i]);
/******/ 	var parentJsonpFunction = oldJsonpFunction;
/******/
/******/
/******/ 	// add entry module to deferred list
/******/ 	deferredModules.push(["./CTFd/themes/admin/assets/js/pages/notifications.js","helpers","vendor","default~pages/challenge~pages/challenges~pages/configs~pages/editor~pages/main~pages/notifications~p~d5a3cc0a"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "./CTFd/themes/admin/assets/js/components/notifications/Notification.vue":
/*!*******************************************************************************!*\
  !*** ./CTFd/themes/admin/assets/js/components/notifications/Notification.vue ***!
  \*******************************************************************************/
/*! no static exports found */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

;
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./Notification.vue?vue&type=template&id=e5ef5b64& */ \"./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64&\");\n/* harmony import */ var _Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./Notification.vue?vue&type=script&lang=js& */ \"./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js&\");\n/* harmony reexport (unknown) */ for(var __WEBPACK_IMPORT_KEY__ in _Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__) if(__WEBPACK_IMPORT_KEY__ !== 'default') (function(key) { __webpack_require__.d(__webpack_exports__, key, function() { return _Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[key]; }) }(__WEBPACK_IMPORT_KEY__));\n/* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../../../../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ \"./node_modules/vue-loader/lib/runtime/componentNormalizer.js\");\n\n\n\n\n\n/* normalize component */\n\nvar component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__[\"default\"])(\n  _Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[\"default\"],\n  _Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__[\"render\"],\n  _Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"],\n  false,\n  null,\n  null,\n  null\n  \n)\n\n/* hot reload */\nif (false) { var api; }\ncomponent.options.__file = \"CTFd/themes/admin/assets/js/components/notifications/Notification.vue\"\n/* harmony default export */ __webpack_exports__[\"default\"] = (component.exports);\n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?");

/***/ }),

/***/ "./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js&":
/*!********************************************************************************************************!*\
  !*** ./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js& ***!
  \********************************************************************************************************/
/*! no static exports found */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

;
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../../../../node_modules/babel-loader/lib??ref--0!../../../../../../../node_modules/vue-loader/lib??vue-loader-options!./Notification.vue?vue&type=script&lang=js& */ \"./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/index.js?!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js&\");\n/* harmony import */ var _node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__);\n/* harmony reexport (unknown) */ for(var __WEBPACK_IMPORT_KEY__ in _node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__) if(__WEBPACK_IMPORT_KEY__ !== 'default') (function(key) { __webpack_require__.d(__webpack_exports__, key, function() { return _node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__[key]; }) }(__WEBPACK_IMPORT_KEY__));\n /* harmony default export */ __webpack_exports__[\"default\"] = (_node_modules_babel_loader_lib_index_js_ref_0_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0___default.a); \n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?");

/***/ }),

/***/ "./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64&":
/*!**************************************************************************************************************!*\
  !*** ./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64& ***!
  \**************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

;
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../../../../node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!../../../../../../../node_modules/vue-loader/lib??vue-loader-options!./Notification.vue?vue&type=template&id=e5ef5b64& */ \"./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__[\"render\"]; });\n\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_Notification_vue_vue_type_template_id_e5ef5b64___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"]; });\n\n\n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?");

/***/ }),

/***/ "./CTFd/themes/admin/assets/js/pages/notifications.js":
/*!************************************************************!*\
  !*** ./CTFd/themes/admin/assets/js/pages/notifications.js ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

;
eval("\n\n__webpack_require__(/*! ./main */ \"./CTFd/themes/admin/assets/js/pages/main.js\");\n\n__webpack_require__(/*! core/utils */ \"./CTFd/themes/pages/assets/js/utils.js\");\n\nvar _jquery = _interopRequireDefault(__webpack_require__(/*! jquery */ \"./node_modules/jquery/dist/jquery.js\"));\n\nvar _CTFd = _interopRequireDefault(__webpack_require__(/*! core/CTFd */ \"./CTFd/themes/pages/assets/js/CTFd.js\"));\n\nvar _ezq = __webpack_require__(/*! core/ezq */ \"./CTFd/themes/pages/assets/js/ezq.js\");\n\nvar _vueEsm = _interopRequireDefault(__webpack_require__(/*! vue/dist/vue.esm.browser */ \"./node_modules/vue/dist/vue.esm.browser.js\"));\n\nvar _Notification = _interopRequireDefault(__webpack_require__(/*! ../components/notifications/Notification.vue */ \"./CTFd/themes/admin/assets/js/components/notifications/Notification.vue\"));\n\nfunction _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }\n\nvar notificationCard = _vueEsm.default.extend(_Notification.default);\n\nfunction submit(event) {\n  event.preventDefault();\n  var $form = (0, _jquery.default)(this);\n  var params = $form.serializeJSON(); // Disable button after click\n\n  $form.find(\"button[type=submit]\").attr(\"disabled\", true);\n\n  _CTFd.default.api.post_notification_list({}, params).then(response => {\n    $form.find(\":input[name=title]\").val(\"\");\n    $form.find(\":input[name=content]\").val(\"\"); // Admin should also see the notification sent out\n\n    setTimeout(function () {\n      $form.find(\"button[type=submit]\").attr(\"disabled\", false);\n    }, 1000);\n\n    if (!response.success) {\n      (0, _ezq.ezAlert)({\n        title: \"Error\",\n        body: \"Could not send notification. Please try again.\",\n        button: \"OK\"\n      });\n    }\n\n    var vueContainer = document.createElement(\"div\");\n    (0, _jquery.default)(\"#notifications-list\").prepend(vueContainer);\n    new notificationCard({\n      propsData: {\n        id: response.data.id,\n        title: response.data.title,\n        content: response.data.content,\n        html: response.data.html,\n        date: response.data.date\n      }\n    }).$mount(vueContainer);\n  });\n}\n\nfunction deleteNotification(event) {\n  event.preventDefault();\n  var $elem = (0, _jquery.default)(this);\n  var id = $elem.data(\"notif-id\");\n\n  if (confirm(\"Are you sure you want to delete this notification?\")) {\n    _CTFd.default.api.delete_notification({\n      notificationId: id\n    }).then(response => {\n      if (response.success) {\n        $elem.parent().remove();\n      }\n    });\n  }\n}\n\n(0, _jquery.default)(() => {\n  (0, _jquery.default)(\"#notifications_form\").submit(submit);\n  (0, _jquery.default)(\".delete-notification\").click(deleteNotification);\n});\n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/pages/notifications.js?");

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js?!./node_modules/vue-loader/lib/index.js?!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js&":
/*!**************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib??ref--0!./node_modules/vue-loader/lib??vue-loader-options!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=script&lang=js& ***!
  \**************************************************************************************************************************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

;
eval("\n\nObject.defineProperty(exports, \"__esModule\", {\n  value: true\n});\nexports.default = void 0;\n\nvar _CTFd = _interopRequireDefault(__webpack_require__(/*! core/CTFd */ \"./CTFd/themes/pages/assets/js/CTFd.js\"));\n\nvar _dayjs = _interopRequireDefault(__webpack_require__(/*! dayjs */ \"./node_modules/dayjs/dayjs.min.js\"));\n\nvar _highlight = _interopRequireDefault(__webpack_require__(/*! highlight.js */ \"./node_modules/highlight.js/lib/index.js\"));\n\nfunction _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }\n\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\nvar _default = {\n  props: {\n    id: Number,\n    title: String,\n    content: String,\n    html: String,\n    date: String\n  },\n  methods: {\n    localDate: function localDate() {\n      return (0, _dayjs.default)(this.date).format(\"MMMM Do, h:mm:ss A\");\n    },\n    deleteNotification: function deleteNotification() {\n      if (confirm(\"Are you sure you want to delete this notification?\")) {\n        _CTFd.default.api.delete_notification({\n          notificationId: this.id\n        }).then(response => {\n          if (response.success) {\n            // Delete the current component\n            // https://stackoverflow.com/a/55384005\n            this.$destroy();\n            this.$el.parentNode.removeChild(this.$el);\n          }\n        });\n      }\n    }\n  },\n\n  mounted() {\n    this.$el.querySelectorAll(\"pre code\").forEach(block => {\n      _highlight.default.highlightBlock(block);\n    });\n  }\n\n};\nexports.default = _default;\n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?./node_modules/babel-loader/lib??ref--0!./node_modules/vue-loader/lib??vue-loader-options");

/***/ }),

/***/ "./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64&":
/*!********************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options!./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?vue&type=template&id=e5ef5b64& ***!
  \********************************************************************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

;
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return render; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return staticRenderFns; });\nvar render = function() {\n  var _vm = this\n  var _h = _vm.$createElement\n  var _c = _vm._self._c || _h\n  return _c(\"div\", { staticClass: \"card bg-light mb-4\" }, [\n    _c(\n      \"button\",\n      {\n        staticClass: \"delete-notification close position-absolute p-3\",\n        staticStyle: { right: \"0\" },\n        attrs: {\n          type: \"button\",\n          \"data-notif-id\": this.id,\n          \"data-dismiss\": \"alert\",\n          \"aria-label\": \"Close\"\n        },\n        on: {\n          click: function($event) {\n            return _vm.deleteNotification()\n          }\n        }\n      },\n      [_c(\"span\", { attrs: { \"aria-hidden\": \"true\" } }, [_vm._v(\"×\")])]\n    ),\n    _vm._v(\" \"),\n    _c(\"div\", { staticClass: \"card-body\" }, [\n      _c(\"h3\", { staticClass: \"card-title\" }, [_vm._v(_vm._s(_vm.title))]),\n      _vm._v(\" \"),\n      _c(\"blockquote\", { staticClass: \"blockquote mb-0\" }, [\n        _c(\"p\", { domProps: { innerHTML: _vm._s(this.html) } }),\n        _vm._v(\" \"),\n        _c(\"small\", { staticClass: \"text-muted\" }, [\n          _c(\"span\", { attrs: { \"data-time\": this.date } }, [\n            _vm._v(_vm._s(this.localDate()))\n          ])\n        ])\n      ])\n    ])\n  ])\n}\nvar staticRenderFns = []\nrender._withStripped = true\n\n\n\n//# sourceURL=webpack:///./CTFd/themes/admin/assets/js/components/notifications/Notification.vue?./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options");

/***/ })

/******/ });