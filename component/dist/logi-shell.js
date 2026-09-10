//#region \0rolldown/runtime.js
var e = Object.create, t = Object.defineProperty, n = Object.getOwnPropertyDescriptor, r = Object.getOwnPropertyNames, i = Object.getPrototypeOf, a = Object.prototype.hasOwnProperty, o = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), s = (e, i, o, s) => {
	if (i && typeof i == "object" || typeof i == "function") for (var c = r(i), l = 0, u = c.length, d; l < u; l++) d = c[l], !a.call(e, d) && d !== o && t(e, d, {
		get: ((e) => i[e]).bind(null, d),
		enumerable: !(s = n(i, d)) || s.enumerable
	});
	return e;
}, c = (n, r, o) => (o = n == null ? {} : e(i(n)), s(r || !n || !n.__esModule || !a.call(n, "default") ? t(o, "default", {
	value: n,
	enumerable: !0
}) : o, n)), l = /* @__PURE__ */ o(((e) => {
	var t = Symbol.for("react.transitional.element"), n = Symbol.for("react.portal"), r = Symbol.for("react.fragment"), i = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), o = Symbol.for("react.consumer"), s = Symbol.for("react.context"), c = Symbol.for("react.forward_ref"), l = Symbol.for("react.suspense"), u = Symbol.for("react.memo"), d = Symbol.for("react.lazy"), f = Symbol.for("react.activity"), p = Symbol.iterator;
	function m(e) {
		return typeof e != "object" || !e ? null : (e = p && e[p] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var h = {
		isMounted: function() {
			return !1;
		},
		enqueueForceUpdate: function() {},
		enqueueReplaceState: function() {},
		enqueueSetState: function() {}
	}, g = Object.assign, _ = {};
	function v(e, t, n) {
		this.props = e, this.context = t, this.refs = _, this.updater = n || h;
	}
	v.prototype.isReactComponent = {}, v.prototype.setState = function(e, t) {
		if (typeof e != "object" && typeof e != "function" && e != null) throw Error("takes an object of state variables to update or a function which returns an object of state variables.");
		this.updater.enqueueSetState(this, e, t, "setState");
	}, v.prototype.forceUpdate = function(e) {
		this.updater.enqueueForceUpdate(this, e, "forceUpdate");
	};
	function y() {}
	y.prototype = v.prototype;
	function b(e, t, n) {
		this.props = e, this.context = t, this.refs = _, this.updater = n || h;
	}
	var x = b.prototype = new y();
	x.constructor = b, g(x, v.prototype), x.isPureReactComponent = !0;
	var S = Array.isArray;
	function C() {}
	var w = {
		H: null,
		A: null,
		T: null,
		S: null
	}, T = Object.prototype.hasOwnProperty;
	function E(e, n, r) {
		var i = r.ref;
		return {
			$$typeof: t,
			type: e,
			key: n,
			ref: i === void 0 ? null : i,
			props: r
		};
	}
	function D(e, t) {
		return E(e.type, t, e.props);
	}
	function O(e) {
		return typeof e == "object" && !!e && e.$$typeof === t;
	}
	function k(e) {
		var t = {
			"=": "=0",
			":": "=2"
		};
		return "$" + e.replace(/[=:]/g, function(e) {
			return t[e];
		});
	}
	var ee = /\/+/g;
	function te(e, t) {
		return typeof e == "object" && e && e.key != null ? k("" + e.key) : t.toString(36);
	}
	function ne(e) {
		switch (e.status) {
			case "fulfilled": return e.value;
			case "rejected": throw e.reason;
			default: switch (typeof e.status == "string" ? e.then(C, C) : (e.status = "pending", e.then(function(t) {
				e.status === "pending" && (e.status = "fulfilled", e.value = t);
			}, function(t) {
				e.status === "pending" && (e.status = "rejected", e.reason = t);
			})), e.status) {
				case "fulfilled": return e.value;
				case "rejected": throw e.reason;
			}
		}
		throw e;
	}
	function re(e, r, i, a, o) {
		var s = typeof e;
		(s === "undefined" || s === "boolean") && (e = null);
		var c = !1;
		if (e === null) c = !0;
		else switch (s) {
			case "bigint":
			case "string":
			case "number":
				c = !0;
				break;
			case "object": switch (e.$$typeof) {
				case t:
				case n:
					c = !0;
					break;
				case d: return c = e._init, re(c(e._payload), r, i, a, o);
			}
		}
		if (c) return o = o(e), c = a === "" ? "." + te(e, 0) : a, S(o) ? (i = "", c != null && (i = c.replace(ee, "$&/") + "/"), re(o, r, i, "", function(e) {
			return e;
		})) : o != null && (O(o) && (o = D(o, i + (o.key == null || e && e.key === o.key ? "" : ("" + o.key).replace(ee, "$&/") + "/") + c)), r.push(o)), 1;
		c = 0;
		var l = a === "" ? "." : a + ":";
		if (S(e)) for (var u = 0; u < e.length; u++) a = e[u], s = l + te(a, u), c += re(a, r, i, s, o);
		else if (u = m(e), typeof u == "function") for (e = u.call(e), u = 0; !(a = e.next()).done;) a = a.value, s = l + te(a, u++), c += re(a, r, i, s, o);
		else if (s === "object") {
			if (typeof e.then == "function") return re(ne(e), r, i, a, o);
			throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		}
		return c;
	}
	function ie(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return re(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function A(e) {
		if (e._status === -1) {
			var t = e._result;
			t = t(), t.then(function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 1, e._result = t);
			}, function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 2, e._result = t);
			}), e._status === -1 && (e._status = 0, e._result = t);
		}
		if (e._status === 1) return e._result.default;
		throw e._result;
	}
	var j = typeof reportError == "function" ? reportError : function(e) {
		if (typeof window == "object" && typeof window.ErrorEvent == "function") {
			var t = new window.ErrorEvent("error", {
				bubbles: !0,
				cancelable: !0,
				message: typeof e == "object" && e && typeof e.message == "string" ? String(e.message) : String(e),
				error: e
			});
			if (!window.dispatchEvent(t)) return;
		}
		console.error(e);
	}, M = {
		map: ie,
		forEach: function(e, t, n) {
			ie(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return ie(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return ie(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!O(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	};
	e.Activity = f, e.Children = M, e.Component = v, e.Fragment = r, e.Profiler = a, e.PureComponent = b, e.StrictMode = i, e.Suspense = l, e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = w, e.__COMPILER_RUNTIME = {
		__proto__: null,
		c: function(e) {
			return w.H.useMemoCache(e);
		}
	}, e.cache = function(e) {
		return function() {
			return e.apply(null, arguments);
		};
	}, e.cacheSignal = function() {
		return null;
	}, e.cloneElement = function(e, t, n) {
		if (e == null) throw Error("The argument must be a React element, but you passed " + e + ".");
		var r = g({}, e.props), i = e.key;
		if (t != null) for (a in t.key !== void 0 && (i = "" + t.key), t) !T.call(t, a) || a === "key" || a === "__self" || a === "__source" || a === "ref" && t.ref === void 0 || (r[a] = t[a]);
		var a = arguments.length - 2;
		if (a === 1) r.children = n;
		else if (1 < a) {
			for (var o = Array(a), s = 0; s < a; s++) o[s] = arguments[s + 2];
			r.children = o;
		}
		return E(e.type, i, r);
	}, e.createContext = function(e) {
		return e = {
			$$typeof: s,
			_currentValue: e,
			_currentValue2: e,
			_threadCount: 0,
			Provider: null,
			Consumer: null
		}, e.Provider = e, e.Consumer = {
			$$typeof: o,
			_context: e
		}, e;
	}, e.createElement = function(e, t, n) {
		var r, i = {}, a = null;
		if (t != null) for (r in t.key !== void 0 && (a = "" + t.key), t) T.call(t, r) && r !== "key" && r !== "__self" && r !== "__source" && (i[r] = t[r]);
		var o = arguments.length - 2;
		if (o === 1) i.children = n;
		else if (1 < o) {
			for (var s = Array(o), c = 0; c < o; c++) s[c] = arguments[c + 2];
			i.children = s;
		}
		if (e && e.defaultProps) for (r in o = e.defaultProps, o) i[r] === void 0 && (i[r] = o[r]);
		return E(e, a, i);
	}, e.createRef = function() {
		return { current: null };
	}, e.forwardRef = function(e) {
		return {
			$$typeof: c,
			render: e
		};
	}, e.isValidElement = O, e.lazy = function(e) {
		return {
			$$typeof: d,
			_payload: {
				_status: -1,
				_result: e
			},
			_init: A
		};
	}, e.memo = function(e, t) {
		return {
			$$typeof: u,
			type: e,
			compare: t === void 0 ? null : t
		};
	}, e.startTransition = function(e) {
		var t = w.T, n = {};
		w.T = n;
		try {
			var r = e(), i = w.S;
			i !== null && i(n, r), typeof r == "object" && r && typeof r.then == "function" && r.then(C, j);
		} catch (e) {
			j(e);
		} finally {
			t !== null && n.types !== null && (t.types = n.types), w.T = t;
		}
	}, e.unstable_useCacheRefresh = function() {
		return w.H.useCacheRefresh();
	}, e.use = function(e) {
		return w.H.use(e);
	}, e.useActionState = function(e, t, n) {
		return w.H.useActionState(e, t, n);
	}, e.useCallback = function(e, t) {
		return w.H.useCallback(e, t);
	}, e.useContext = function(e) {
		return w.H.useContext(e);
	}, e.useDebugValue = function() {}, e.useDeferredValue = function(e, t) {
		return w.H.useDeferredValue(e, t);
	}, e.useEffect = function(e, t) {
		return w.H.useEffect(e, t);
	}, e.useEffectEvent = function(e) {
		return w.H.useEffectEvent(e);
	}, e.useId = function() {
		return w.H.useId();
	}, e.useImperativeHandle = function(e, t, n) {
		return w.H.useImperativeHandle(e, t, n);
	}, e.useInsertionEffect = function(e, t) {
		return w.H.useInsertionEffect(e, t);
	}, e.useLayoutEffect = function(e, t) {
		return w.H.useLayoutEffect(e, t);
	}, e.useMemo = function(e, t) {
		return w.H.useMemo(e, t);
	}, e.useOptimistic = function(e, t) {
		return w.H.useOptimistic(e, t);
	}, e.useReducer = function(e, t, n) {
		return w.H.useReducer(e, t, n);
	}, e.useRef = function(e) {
		return w.H.useRef(e);
	}, e.useState = function(e) {
		return w.H.useState(e);
	}, e.useSyncExternalStore = function(e, t, n) {
		return w.H.useSyncExternalStore(e, t, n);
	}, e.useTransition = function() {
		return w.H.useTransition();
	}, e.version = "19.2.8";
})), u = /* @__PURE__ */ o(((e, t) => {
	t.exports = l();
})), d = /* @__PURE__ */ o(((e) => {
	function t(e, t) {
		var n = e.length;
		e.push(t);
		a: for (; 0 < n;) {
			var r = n - 1 >>> 1, a = e[r];
			if (0 < i(a, t)) e[r] = t, e[n] = a, n = r;
			else break a;
		}
	}
	function n(e) {
		return e.length === 0 ? null : e[0];
	}
	function r(e) {
		if (e.length === 0) return null;
		var t = e[0], n = e.pop();
		if (n !== t) {
			e[0] = n;
			a: for (var r = 0, a = e.length, o = a >>> 1; r < o;) {
				var s = 2 * (r + 1) - 1, c = e[s], l = s + 1, u = e[l];
				if (0 > i(c, n)) l < a && 0 > i(u, c) ? (e[r] = u, e[l] = n, r = l) : (e[r] = c, e[s] = n, r = s);
				else if (l < a && 0 > i(u, n)) e[r] = u, e[l] = n, r = l;
				else break a;
			}
		}
		return t;
	}
	function i(e, t) {
		var n = e.sortIndex - t.sortIndex;
		return n === 0 ? e.id - t.id : n;
	}
	if (e.unstable_now = void 0, typeof performance == "object" && typeof performance.now == "function") {
		var a = performance;
		e.unstable_now = function() {
			return a.now();
		};
	} else {
		var o = Date, s = o.now();
		e.unstable_now = function() {
			return o.now() - s;
		};
	}
	var c = [], l = [], u = 1, d = null, f = 3, p = !1, m = !1, h = !1, g = !1, _ = typeof setTimeout == "function" ? setTimeout : null, v = typeof clearTimeout == "function" ? clearTimeout : null, y = typeof setImmediate < "u" ? setImmediate : null;
	function b(e) {
		for (var i = n(l); i !== null;) {
			if (i.callback === null) r(l);
			else if (i.startTime <= e) r(l), i.sortIndex = i.expirationTime, t(c, i);
			else break;
			i = n(l);
		}
	}
	function x(e) {
		if (h = !1, b(e), !m) {
			if (n(c) !== null) m = !0, S || (S = !0, O());
			else {
				var t = n(l);
				t !== null && te(x, t.startTime - e);
			}
		}
	}
	var S = !1, C = -1, w = 5, T = -1;
	function E() {
		return g ? !0 : !(e.unstable_now() - T < w);
	}
	function D() {
		if (g = !1, S) {
			var t = e.unstable_now();
			T = t;
			var i = !0;
			try {
				a: {
					m = !1, h && (h = !1, v(C), C = -1), p = !0;
					var a = f;
					try {
						b: {
							for (b(t), d = n(c); d !== null && !(d.expirationTime > t && E());) {
								var o = d.callback;
								if (typeof o == "function") {
									d.callback = null, f = d.priorityLevel;
									var s = o(d.expirationTime <= t);
									if (t = e.unstable_now(), typeof s == "function") {
										d.callback = s, b(t), i = !0;
										break b;
									}
									d === n(c) && r(c), b(t);
								} else r(c);
								d = n(c);
							}
							if (d !== null) i = !0;
							else {
								var u = n(l);
								u !== null && te(x, u.startTime - t), i = !1;
							}
						}
						break a;
					} finally {
						d = null, f = a, p = !1;
					}
					i = void 0;
				}
			} finally {
				i ? O() : S = !1;
			}
		}
	}
	var O;
	if (typeof y == "function") O = function() {
		y(D);
	};
	else if (typeof MessageChannel < "u") {
		var k = new MessageChannel(), ee = k.port2;
		k.port1.onmessage = D, O = function() {
			ee.postMessage(null);
		};
	} else O = function() {
		_(D, 0);
	};
	function te(t, n) {
		C = _(function() {
			t(e.unstable_now());
		}, n);
	}
	e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(e) {
		e.callback = null;
	}, e.unstable_forceFrameRate = function(e) {
		0 > e || 125 < e ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : w = 0 < e ? Math.floor(1e3 / e) : 5;
	}, e.unstable_getCurrentPriorityLevel = function() {
		return f;
	}, e.unstable_next = function(e) {
		switch (f) {
			case 1:
			case 2:
			case 3:
				var t = 3;
				break;
			default: t = f;
		}
		var n = f;
		f = t;
		try {
			return e();
		} finally {
			f = n;
		}
	}, e.unstable_requestPaint = function() {
		g = !0;
	}, e.unstable_runWithPriority = function(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 3:
			case 4:
			case 5: break;
			default: e = 3;
		}
		var n = f;
		f = e;
		try {
			return t();
		} finally {
			f = n;
		}
	}, e.unstable_scheduleCallback = function(r, i, a) {
		var o = e.unstable_now();
		switch (typeof a == "object" && a ? (a = a.delay, a = typeof a == "number" && 0 < a ? o + a : o) : a = o, r) {
			case 1:
				var s = -1;
				break;
			case 2:
				s = 250;
				break;
			case 5:
				s = 1073741823;
				break;
			case 4:
				s = 1e4;
				break;
			default: s = 5e3;
		}
		return s = a + s, r = {
			id: u++,
			callback: i,
			priorityLevel: r,
			startTime: a,
			expirationTime: s,
			sortIndex: -1
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (v(C), C = -1) : h = !0, te(x, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, S || (S = !0, O()))), r;
	}, e.unstable_shouldYield = E, e.unstable_wrapCallback = function(e) {
		var t = f;
		return function() {
			var n = f;
			f = t;
			try {
				return e.apply(this, arguments);
			} finally {
				f = n;
			}
		};
	};
})), f = /* @__PURE__ */ o(((e, t) => {
	t.exports = d();
})), p = /* @__PURE__ */ o(((e) => {
	var t = u();
	function n(e) {
		var t = "https://react.dev/errors/" + e;
		if (1 < arguments.length) {
			t += "?args[]=" + encodeURIComponent(arguments[1]);
			for (var n = 2; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		}
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	function r() {}
	var i = {
		d: {
			f: r,
			r: function() {
				throw Error(n(522));
			},
			D: r,
			C: r,
			L: r,
			m: r,
			X: r,
			S: r,
			M: r
		},
		p: 0,
		findDOMNode: null
	}, a = Symbol.for("react.portal");
	function o(e, t, n) {
		var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
		return {
			$$typeof: a,
			key: r == null ? null : "" + r,
			children: e,
			containerInfo: t,
			implementation: n
		};
	}
	var s = t.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;
	function c(e, t) {
		if (e === "font") return "";
		if (typeof t == "string") return t === "use-credentials" ? t : "";
	}
	e.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = i, e.createPortal = function(e, t) {
		var r = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!t || t.nodeType !== 1 && t.nodeType !== 9 && t.nodeType !== 11) throw Error(n(299));
		return o(e, t, null, r);
	}, e.flushSync = function(e) {
		var t = s.T, n = i.p;
		try {
			if (s.T = null, i.p = 2, e) return e();
		} finally {
			s.T = t, i.p = n, i.d.f();
		}
	}, e.preconnect = function(e, t) {
		typeof e == "string" && (t ? (t = t.crossOrigin, t = typeof t == "string" ? t === "use-credentials" ? t : "" : void 0) : t = null, i.d.C(e, t));
	}, e.prefetchDNS = function(e) {
		typeof e == "string" && i.d.D(e);
	}, e.preinit = function(e, t) {
		if (typeof e == "string" && t && typeof t.as == "string") {
			var n = t.as, r = c(n, t.crossOrigin), a = typeof t.integrity == "string" ? t.integrity : void 0, o = typeof t.fetchPriority == "string" ? t.fetchPriority : void 0;
			n === "style" ? i.d.S(e, typeof t.precedence == "string" ? t.precedence : void 0, {
				crossOrigin: r,
				integrity: a,
				fetchPriority: o
			}) : n === "script" && i.d.X(e, {
				crossOrigin: r,
				integrity: a,
				fetchPriority: o,
				nonce: typeof t.nonce == "string" ? t.nonce : void 0
			});
		}
	}, e.preinitModule = function(e, t) {
		if (typeof e == "string") {
			if (typeof t == "object" && t) {
				if (t.as == null || t.as === "script") {
					var n = c(t.as, t.crossOrigin);
					i.d.M(e, {
						crossOrigin: n,
						integrity: typeof t.integrity == "string" ? t.integrity : void 0,
						nonce: typeof t.nonce == "string" ? t.nonce : void 0
					});
				}
			} else t ?? i.d.M(e);
		}
	}, e.preload = function(e, t) {
		if (typeof e == "string" && typeof t == "object" && t && typeof t.as == "string") {
			var n = t.as, r = c(n, t.crossOrigin);
			i.d.L(e, n, {
				crossOrigin: r,
				integrity: typeof t.integrity == "string" ? t.integrity : void 0,
				nonce: typeof t.nonce == "string" ? t.nonce : void 0,
				type: typeof t.type == "string" ? t.type : void 0,
				fetchPriority: typeof t.fetchPriority == "string" ? t.fetchPriority : void 0,
				referrerPolicy: typeof t.referrerPolicy == "string" ? t.referrerPolicy : void 0,
				imageSrcSet: typeof t.imageSrcSet == "string" ? t.imageSrcSet : void 0,
				imageSizes: typeof t.imageSizes == "string" ? t.imageSizes : void 0,
				media: typeof t.media == "string" ? t.media : void 0
			});
		}
	}, e.preloadModule = function(e, t) {
		if (typeof e == "string") {
			if (t) {
				var n = c(t.as, t.crossOrigin);
				i.d.m(e, {
					as: typeof t.as == "string" && t.as !== "script" ? t.as : void 0,
					crossOrigin: n,
					integrity: typeof t.integrity == "string" ? t.integrity : void 0
				});
			} else i.d.m(e);
		}
	}, e.requestFormReset = function(e) {
		i.d.r(e);
	}, e.unstable_batchedUpdates = function(e, t) {
		return e(t);
	}, e.useFormState = function(e, t, n) {
		return s.H.useFormState(e, t, n);
	}, e.useFormStatus = function() {
		return s.H.useHostTransitionStatus();
	}, e.version = "19.2.8";
})), m = /* @__PURE__ */ o(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = p();
})), h = /* @__PURE__ */ o(((e) => {
	var t = f(), n = u(), r = m();
	function i(e) {
		var t = "https://react.dev/errors/" + e;
		if (1 < arguments.length) {
			t += "?args[]=" + encodeURIComponent(arguments[1]);
			for (var n = 2; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		}
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	function a(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
	}
	function o(e) {
		var t = e, n = e;
		if (e.alternate) for (; t.return;) t = t.return;
		else {
			e = t;
			do
				t = e, t.flags & 4098 && (n = t.return), e = t.return;
			while (e);
		}
		return t.tag === 3 ? n : null;
	}
	function s(e) {
		if (e.tag === 13) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function c(e) {
		if (e.tag === 31) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function l(e) {
		if (o(e) !== e) throw Error(i(188));
	}
	function d(e) {
		var t = e.alternate;
		if (!t) {
			if (t = o(e), t === null) throw Error(i(188));
			return t === e ? e : null;
		}
		for (var n = e, r = t;;) {
			var a = n.return;
			if (a === null) break;
			var s = a.alternate;
			if (s === null) {
				if (r = a.return, r !== null) {
					n = r;
					continue;
				}
				break;
			}
			if (a.child === s.child) {
				for (s = a.child; s;) {
					if (s === n) return l(a), e;
					if (s === r) return l(a), t;
					s = s.sibling;
				}
				throw Error(i(188));
			}
			if (n.return !== r.return) n = a, r = s;
			else {
				for (var c = !1, u = a.child; u;) {
					if (u === n) {
						c = !0, n = a, r = s;
						break;
					}
					if (u === r) {
						c = !0, r = a, n = s;
						break;
					}
					u = u.sibling;
				}
				if (!c) {
					for (u = s.child; u;) {
						if (u === n) {
							c = !0, n = s, r = a;
							break;
						}
						if (u === r) {
							c = !0, r = s, n = a;
							break;
						}
						u = u.sibling;
					}
					if (!c) throw Error(i(189));
				}
			}
			if (n.alternate !== r) throw Error(i(190));
		}
		if (n.tag !== 3) throw Error(i(188));
		return n.stateNode.current === n ? e : t;
	}
	function p(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e;
		for (e = e.child; e !== null;) {
			if (t = p(e), t !== null) return t;
			e = e.sibling;
		}
		return null;
	}
	var h = Object.assign, g = Symbol.for("react.element"), _ = Symbol.for("react.transitional.element"), v = Symbol.for("react.portal"), y = Symbol.for("react.fragment"), b = Symbol.for("react.strict_mode"), x = Symbol.for("react.profiler"), S = Symbol.for("react.consumer"), C = Symbol.for("react.context"), w = Symbol.for("react.forward_ref"), T = Symbol.for("react.suspense"), E = Symbol.for("react.suspense_list"), D = Symbol.for("react.memo"), O = Symbol.for("react.lazy"), k = Symbol.for("react.activity"), ee = Symbol.for("react.memo_cache_sentinel"), te = Symbol.iterator;
	function ne(e) {
		return typeof e != "object" || !e ? null : (e = te && e[te] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var re = Symbol.for("react.client.reference");
	function ie(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.$$typeof === re ? null : e.displayName || e.name || null;
		if (typeof e == "string") return e;
		switch (e) {
			case y: return "Fragment";
			case x: return "Profiler";
			case b: return "StrictMode";
			case T: return "Suspense";
			case E: return "SuspenseList";
			case k: return "Activity";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case v: return "Portal";
			case C: return e.displayName || "Context";
			case S: return (e._context.displayName || "Context") + ".Consumer";
			case w:
				var t = e.render;
				return e = e.displayName, e || (e = t.displayName || t.name || "", e = e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case D: return t = e.displayName || null, t === null ? ie(e.type) || "Memo" : t;
			case O:
				t = e._payload, e = e._init;
				try {
					return ie(e(t));
				} catch {}
		}
		return null;
	}
	var A = Array.isArray, j = n.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, M = r.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, ae = {
		pending: !1,
		data: null,
		method: null,
		action: null
	}, oe = [], se = -1;
	function ce(e) {
		return { current: e };
	}
	function le(e) {
		0 > se || (e.current = oe[se], oe[se] = null, se--);
	}
	function N(e, t) {
		se++, oe[se] = e.current, e.current = t;
	}
	var ue = ce(null), de = ce(null), fe = ce(null), pe = ce(null);
	function me(e, t) {
		switch (N(fe, t), N(de, e), N(ue, null), t.nodeType) {
			case 9:
			case 11:
				e = (e = t.documentElement) && (e = e.namespaceURI) ? Vd(e) : 0;
				break;
			default: if (e = t.tagName, t = t.namespaceURI) t = Vd(t), e = Hd(t, e);
			else switch (e) {
				case "svg":
					e = 1;
					break;
				case "math":
					e = 2;
					break;
				default: e = 0;
			}
		}
		le(ue), N(ue, e);
	}
	function he() {
		le(ue), le(de), le(fe);
	}
	function ge(e) {
		e.memoizedState !== null && N(pe, e);
		var t = ue.current, n = Hd(t, e.type);
		t !== n && (N(de, e), N(ue, n));
	}
	function _e(e) {
		de.current === e && (le(ue), le(de)), pe.current === e && (le(pe), Qf._currentValue = ae);
	}
	var ve, ye;
	function be(e) {
		if (ve === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			ve = t && t[1] || "", ye = -1 < e.stack.indexOf("\n    at") ? " (<anonymous>)" : -1 < e.stack.indexOf("@") ? "@unknown:0:0" : "";
		}
		return "\n" + ve + e + ye;
	}
	var xe = !1;
	function Se(e, t) {
		if (!e || xe) return "";
		xe = !0;
		var n = Error.prepareStackTrace;
		Error.prepareStackTrace = void 0;
		try {
			var r = { DetermineComponentFrameRoot: function() {
				try {
					if (t) {
						var n = function() {
							throw Error();
						};
						if (Object.defineProperty(n.prototype, "props", { set: function() {
							throw Error();
						} }), typeof Reflect == "object" && Reflect.construct) {
							try {
								Reflect.construct(n, []);
							} catch (e) {
								var r = e;
							}
							Reflect.construct(e, [], n);
						} else {
							try {
								n.call();
							} catch (e) {
								r = e;
							}
							e.call(n.prototype);
						}
					} else {
						try {
							throw Error();
						} catch (e) {
							r = e;
						}
						(n = e()) && typeof n.catch == "function" && n.catch(function() {});
					}
				} catch (e) {
					if (e && r && typeof e.stack == "string") return [e.stack, r.stack];
				}
				return [null, null];
			} };
			r.DetermineComponentFrameRoot.displayName = "DetermineComponentFrameRoot";
			var i = Object.getOwnPropertyDescriptor(r.DetermineComponentFrameRoot, "name");
			i && i.configurable && Object.defineProperty(r.DetermineComponentFrameRoot, "name", { value: "DetermineComponentFrameRoot" });
			var a = r.DetermineComponentFrameRoot(), o = a[0], s = a[1];
			if (o && s) {
				var c = o.split("\n"), l = s.split("\n");
				for (i = r = 0; r < c.length && !c[r].includes("DetermineComponentFrameRoot");) r++;
				for (; i < l.length && !l[i].includes("DetermineComponentFrameRoot");) i++;
				if (r === c.length || i === l.length) for (r = c.length - 1, i = l.length - 1; 1 <= r && 0 <= i && c[r] !== l[i];) i--;
				for (; 1 <= r && 0 <= i; r--, i--) if (c[r] !== l[i]) {
					if (r !== 1 || i !== 1) do
						if (r--, i--, 0 > i || c[r] !== l[i]) {
							var u = "\n" + c[r].replace(" at new ", " at ");
							return e.displayName && u.includes("<anonymous>") && (u = u.replace("<anonymous>", e.displayName)), u;
						}
					while (1 <= r && 0 <= i);
					break;
				}
			}
		} finally {
			xe = !1, Error.prepareStackTrace = n;
		}
		return (n = e ? e.displayName || e.name : "") ? be(n) : "";
	}
	function Ce(e, t) {
		switch (e.tag) {
			case 26:
			case 27:
			case 5: return be(e.type);
			case 16: return be("Lazy");
			case 13: return e.child !== t && t !== null ? be("Suspense Fallback") : be("Suspense");
			case 19: return be("SuspenseList");
			case 0:
			case 15: return Se(e.type, !1);
			case 11: return Se(e.type.render, !1);
			case 1: return Se(e.type, !0);
			case 31: return be("Activity");
			default: return "";
		}
	}
	function we(e) {
		try {
			var t = "", n = null;
			do
				t += Ce(e, n), n = e, e = e.return;
			while (e);
			return t;
		} catch (e) {
			return "\nError generating stack: " + e.message + "\n" + e.stack;
		}
	}
	var Te = Object.prototype.hasOwnProperty, Ee = t.unstable_scheduleCallback, De = t.unstable_cancelCallback, Oe = t.unstable_shouldYield, ke = t.unstable_requestPaint, Ae = t.unstable_now, je = t.unstable_getCurrentPriorityLevel, Me = t.unstable_ImmediatePriority, Ne = t.unstable_UserBlockingPriority, Pe = t.unstable_NormalPriority, Fe = t.unstable_LowPriority, Ie = t.unstable_IdlePriority, Le = t.log, Re = t.unstable_setDisableYieldValue, ze = null, Be = null;
	function Ve(e) {
		if (typeof Le == "function" && Re(e), Be && typeof Be.setStrictMode == "function") try {
			Be.setStrictMode(ze, e);
		} catch {}
	}
	var He = Math.clz32 ? Math.clz32 : Ge, Ue = Math.log, We = Math.LN2;
	function Ge(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (Ue(e) / We | 0) | 0;
	}
	var Ke = 256, qe = 262144, Je = 4194304;
	function Ye(e) {
		var t = e & 42;
		if (t !== 0) return t;
		switch (e & -e) {
			case 1: return 1;
			case 2: return 2;
			case 4: return 4;
			case 8: return 8;
			case 16: return 16;
			case 32: return 32;
			case 64: return 64;
			case 128: return 128;
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072: return e & 261888;
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return e & 3932160;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432: return e & 62914560;
			case 67108864: return 67108864;
			case 134217728: return 134217728;
			case 268435456: return 268435456;
			case 536870912: return 536870912;
			case 1073741824: return 0;
			default: return e;
		}
	}
	function Xe(e, t, n) {
		var r = e.pendingLanes;
		if (r === 0) return 0;
		var i = 0, a = e.suspendedLanes, o = e.pingedLanes;
		e = e.warmLanes;
		var s = r & 134217727;
		return s === 0 ? (s = r & ~a, s === 0 ? o === 0 ? n || (n = r & ~e, n !== 0 && (i = Ye(n))) : i = Ye(o) : i = Ye(s)) : (r = s & ~a, r === 0 ? (o &= s, o === 0 ? n || (n = s & ~e, n !== 0 && (i = Ye(n))) : i = Ye(o)) : i = Ye(r)), i === 0 ? 0 : t !== 0 && t !== i && (t & a) === 0 && (a = i & -i, n = t & -t, a >= n || a === 32 && n & 4194048) ? t : i;
	}
	function Ze(e, t) {
		return (e.pendingLanes & ~(e.suspendedLanes & ~e.pingedLanes) & t) === 0;
	}
	function Qe(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 4:
			case 8:
			case 64: return t + 250;
			case 16:
			case 32:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return t + 5e3;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432: return -1;
			case 67108864:
			case 134217728:
			case 268435456:
			case 536870912:
			case 1073741824: return -1;
			default: return -1;
		}
	}
	function $e() {
		var e = Je;
		return Je <<= 1, !(Je & 62914560) && (Je = 4194304), e;
	}
	function et(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function tt(e, t) {
		e.pendingLanes |= t, t !== 268435456 && (e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0);
	}
	function nt(e, t, n, r, i, a) {
		var o = e.pendingLanes;
		e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0, e.expiredLanes &= n, e.entangledLanes &= n, e.errorRecoveryDisabledLanes &= n, e.shellSuspendCounter = 0;
		var s = e.entanglements, c = e.expirationTimes, l = e.hiddenUpdates;
		for (n = o & ~n; 0 < n;) {
			var u = 31 - He(n), d = 1 << u;
			s[u] = 0, c[u] = -1;
			var f = l[u];
			if (f !== null) for (l[u] = null, u = 0; u < f.length; u++) {
				var p = f[u];
				p !== null && (p.lane &= -536870913);
			}
			n &= ~d;
		}
		r !== 0 && rt(e, r, 0), a !== 0 && i === 0 && e.tag !== 0 && (e.suspendedLanes |= a & ~(o & ~t));
	}
	function rt(e, t, n) {
		e.pendingLanes |= t, e.suspendedLanes &= ~t;
		var r = 31 - He(t);
		e.entangledLanes |= t, e.entanglements[r] = e.entanglements[r] | 1073741824 | n & 261930;
	}
	function it(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - He(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	function at(e, t) {
		var n = t & -t;
		return n = n & 42 ? 1 : ot(n), (n & (e.suspendedLanes | t)) === 0 ? n : 0;
	}
	function ot(e) {
		switch (e) {
			case 2:
				e = 1;
				break;
			case 8:
				e = 4;
				break;
			case 32:
				e = 16;
				break;
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152:
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
				e = 128;
				break;
			case 268435456:
				e = 134217728;
				break;
			default: e = 0;
		}
		return e;
	}
	function st(e) {
		return e &= -e, 2 < e ? 8 < e ? e & 134217727 ? 32 : 268435456 : 8 : 2;
	}
	function ct() {
		var e = M.p;
		return e === 0 ? (e = window.event, e === void 0 ? 32 : mp(e.type)) : e;
	}
	function lt(e, t) {
		var n = M.p;
		try {
			return M.p = e, t();
		} finally {
			M.p = n;
		}
	}
	var ut = Math.random().toString(36).slice(2), dt = "__reactFiber$" + ut, ft = "__reactProps$" + ut, pt = "__reactContainer$" + ut, mt = "__reactEvents$" + ut, ht = "__reactListeners$" + ut, gt = "__reactHandles$" + ut, _t = "__reactResources$" + ut, vt = "__reactMarker$" + ut;
	function yt(e) {
		delete e[dt], delete e[ft], delete e[mt], delete e[ht], delete e[gt];
	}
	function bt(e) {
		var t = e[dt];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[pt] || n[dt]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = df(e); e !== null;) {
					if (n = e[dt]) return n;
					e = df(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function xt(e) {
		if (e = e[dt] || e[pt]) {
			var t = e.tag;
			if (t === 5 || t === 6 || t === 13 || t === 31 || t === 26 || t === 27 || t === 3) return e;
		}
		return null;
	}
	function St(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e.stateNode;
		throw Error(i(33));
	}
	function Ct(e) {
		var t = e[_t];
		return t || (t = e[_t] = {
			hoistableStyles: /* @__PURE__ */ new Map(),
			hoistableScripts: /* @__PURE__ */ new Map()
		}), t;
	}
	function wt(e) {
		e[vt] = !0;
	}
	var Tt = /* @__PURE__ */ new Set(), Et = {};
	function Dt(e, t) {
		Ot(e, t), Ot(e + "Capture", t);
	}
	function Ot(e, t) {
		for (Et[e] = t, e = 0; e < t.length; e++) Tt.add(t[e]);
	}
	var kt = RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"), At = {}, jt = {};
	function Mt(e) {
		return Te.call(jt, e) ? !0 : Te.call(At, e) ? !1 : kt.test(e) ? jt[e] = !0 : (At[e] = !0, !1);
	}
	function Nt(e, t, n) {
		if (Mt(t)) {
			if (n === null) e.removeAttribute(t);
			else {
				switch (typeof n) {
					case "undefined":
					case "function":
					case "symbol":
						e.removeAttribute(t);
						return;
					case "boolean":
						var r = t.toLowerCase().slice(0, 5);
						if (r !== "data-" && r !== "aria-") {
							e.removeAttribute(t);
							return;
						}
				}
				e.setAttribute(t, "" + n);
			}
		}
	}
	function Pt(e, t, n) {
		if (n === null) e.removeAttribute(t);
		else {
			switch (typeof n) {
				case "undefined":
				case "function":
				case "symbol":
				case "boolean":
					e.removeAttribute(t);
					return;
			}
			e.setAttribute(t, "" + n);
		}
	}
	function Ft(e, t, n, r) {
		if (r === null) e.removeAttribute(n);
		else {
			switch (typeof r) {
				case "undefined":
				case "function":
				case "symbol":
				case "boolean":
					e.removeAttribute(n);
					return;
			}
			e.setAttributeNS(t, n, "" + r);
		}
	}
	function It(e) {
		switch (typeof e) {
			case "bigint":
			case "boolean":
			case "number":
			case "string":
			case "undefined": return e;
			case "object": return e;
			default: return "";
		}
	}
	function Lt(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function Rt(e, t, n) {
		var r = Object.getOwnPropertyDescriptor(e.constructor.prototype, t);
		if (!e.hasOwnProperty(t) && r !== void 0 && typeof r.get == "function" && typeof r.set == "function") {
			var i = r.get, a = r.set;
			return Object.defineProperty(e, t, {
				configurable: !0,
				get: function() {
					return i.call(this);
				},
				set: function(e) {
					n = "" + e, a.call(this, e);
				}
			}), Object.defineProperty(e, t, { enumerable: r.enumerable }), {
				getValue: function() {
					return n;
				},
				setValue: function(e) {
					n = "" + e;
				},
				stopTracking: function() {
					e._valueTracker = null, delete e[t];
				}
			};
		}
	}
	function zt(e) {
		if (!e._valueTracker) {
			var t = Lt(e) ? "checked" : "value";
			e._valueTracker = Rt(e, t, "" + e[t]);
		}
	}
	function Bt(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = Lt(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== n && (t.setValue(e), !0);
	}
	function Vt(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch {
			return e.body;
		}
	}
	var Ht = /[\n"\\]/g;
	function Ut(e) {
		return e.replace(Ht, function(e) {
			return "\\" + e.charCodeAt(0).toString(16) + " ";
		});
	}
	function Wt(e, t, n, r, i, a, o, s) {
		e.name = "", o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" ? e.type = o : e.removeAttribute("type"), t == null ? o !== "submit" && o !== "reset" || e.removeAttribute("value") : o === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + It(t)) : e.value !== "" + It(t) && (e.value = "" + It(t)), t == null ? n == null ? r != null && e.removeAttribute("value") : Kt(e, o, It(n)) : Kt(e, o, It(t)), i == null && a != null && (e.defaultChecked = !!a), i != null && (e.checked = i && typeof i != "function" && typeof i != "symbol"), s != null && typeof s != "function" && typeof s != "symbol" && typeof s != "boolean" ? e.name = "" + It(s) : e.removeAttribute("name");
	}
	function Gt(e, t, n, r, i, a, o, s) {
		if (a != null && typeof a != "function" && typeof a != "symbol" && typeof a != "boolean" && (e.type = a), t != null || n != null) {
			if (!(a !== "submit" && a !== "reset" || t != null)) {
				zt(e);
				return;
			}
			n = n == null ? "" : "" + It(n), t = t == null ? n : "" + It(t), s || t === e.value || (e.value = t), e.defaultValue = t;
		}
		r = r ?? i, r = typeof r != "function" && typeof r != "symbol" && !!r, e.checked = s ? e.checked : !!r, e.defaultChecked = !!r, o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" && (e.name = o), zt(e);
	}
	function Kt(e, t, n) {
		t === "number" && Vt(e.ownerDocument) === e || e.defaultValue === "" + n || (e.defaultValue = "" + n);
	}
	function qt(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + It(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function Jt(e, t, n) {
		if (t != null && (t = "" + It(t), t !== e.value && (e.value = t), n == null)) {
			e.defaultValue !== t && (e.defaultValue = t);
			return;
		}
		e.defaultValue = n == null ? "" : "" + It(n);
	}
	function Yt(e, t, n, r) {
		if (t == null) {
			if (r != null) {
				if (n != null) throw Error(i(92));
				if (A(r)) {
					if (1 < r.length) throw Error(i(93));
					r = r[0];
				}
				n = r;
			}
			n ?? (n = ""), t = n;
		}
		n = It(t), e.defaultValue = n, r = e.textContent, r === n && r !== "" && r !== null && (e.value = r), zt(e);
	}
	function Xt(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var Zt = new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));
	function Qt(e, t, n) {
		var r = t.indexOf("--") === 0;
		n == null || typeof n == "boolean" || n === "" ? r ? e.setProperty(t, "") : t === "float" ? e.cssFloat = "" : e[t] = "" : r ? e.setProperty(t, n) : typeof n != "number" || n === 0 || Zt.has(t) ? t === "float" ? e.cssFloat = n : e[t] = ("" + n).trim() : e[t] = n + "px";
	}
	function $t(e, t, n) {
		if (t != null && typeof t != "object") throw Error(i(62));
		if (e = e.style, n != null) {
			for (var r in n) !n.hasOwnProperty(r) || t != null && t.hasOwnProperty(r) || (r.indexOf("--") === 0 ? e.setProperty(r, "") : r === "float" ? e.cssFloat = "" : e[r] = "");
			for (var a in t) r = t[a], t.hasOwnProperty(a) && n[a] !== r && Qt(e, a, r);
		} else for (var o in t) t.hasOwnProperty(o) && Qt(e, o, t[o]);
	}
	function en(e) {
		if (e.indexOf("-") === -1) return !1;
		switch (e) {
			case "annotation-xml":
			case "color-profile":
			case "font-face":
			case "font-face-src":
			case "font-face-uri":
			case "font-face-format":
			case "font-face-name":
			case "missing-glyph": return !1;
			default: return !0;
		}
	}
	var tn = /* @__PURE__ */ new Map([
		["acceptCharset", "accept-charset"],
		["htmlFor", "for"],
		["httpEquiv", "http-equiv"],
		["crossOrigin", "crossorigin"],
		["accentHeight", "accent-height"],
		["alignmentBaseline", "alignment-baseline"],
		["arabicForm", "arabic-form"],
		["baselineShift", "baseline-shift"],
		["capHeight", "cap-height"],
		["clipPath", "clip-path"],
		["clipRule", "clip-rule"],
		["colorInterpolation", "color-interpolation"],
		["colorInterpolationFilters", "color-interpolation-filters"],
		["colorProfile", "color-profile"],
		["colorRendering", "color-rendering"],
		["dominantBaseline", "dominant-baseline"],
		["enableBackground", "enable-background"],
		["fillOpacity", "fill-opacity"],
		["fillRule", "fill-rule"],
		["floodColor", "flood-color"],
		["floodOpacity", "flood-opacity"],
		["fontFamily", "font-family"],
		["fontSize", "font-size"],
		["fontSizeAdjust", "font-size-adjust"],
		["fontStretch", "font-stretch"],
		["fontStyle", "font-style"],
		["fontVariant", "font-variant"],
		["fontWeight", "font-weight"],
		["glyphName", "glyph-name"],
		["glyphOrientationHorizontal", "glyph-orientation-horizontal"],
		["glyphOrientationVertical", "glyph-orientation-vertical"],
		["horizAdvX", "horiz-adv-x"],
		["horizOriginX", "horiz-origin-x"],
		["imageRendering", "image-rendering"],
		["letterSpacing", "letter-spacing"],
		["lightingColor", "lighting-color"],
		["markerEnd", "marker-end"],
		["markerMid", "marker-mid"],
		["markerStart", "marker-start"],
		["overlinePosition", "overline-position"],
		["overlineThickness", "overline-thickness"],
		["paintOrder", "paint-order"],
		["panose-1", "panose-1"],
		["pointerEvents", "pointer-events"],
		["renderingIntent", "rendering-intent"],
		["shapeRendering", "shape-rendering"],
		["stopColor", "stop-color"],
		["stopOpacity", "stop-opacity"],
		["strikethroughPosition", "strikethrough-position"],
		["strikethroughThickness", "strikethrough-thickness"],
		["strokeDasharray", "stroke-dasharray"],
		["strokeDashoffset", "stroke-dashoffset"],
		["strokeLinecap", "stroke-linecap"],
		["strokeLinejoin", "stroke-linejoin"],
		["strokeMiterlimit", "stroke-miterlimit"],
		["strokeOpacity", "stroke-opacity"],
		["strokeWidth", "stroke-width"],
		["textAnchor", "text-anchor"],
		["textDecoration", "text-decoration"],
		["textRendering", "text-rendering"],
		["transformOrigin", "transform-origin"],
		["underlinePosition", "underline-position"],
		["underlineThickness", "underline-thickness"],
		["unicodeBidi", "unicode-bidi"],
		["unicodeRange", "unicode-range"],
		["unitsPerEm", "units-per-em"],
		["vAlphabetic", "v-alphabetic"],
		["vHanging", "v-hanging"],
		["vIdeographic", "v-ideographic"],
		["vMathematical", "v-mathematical"],
		["vectorEffect", "vector-effect"],
		["vertAdvY", "vert-adv-y"],
		["vertOriginX", "vert-origin-x"],
		["vertOriginY", "vert-origin-y"],
		["wordSpacing", "word-spacing"],
		["writingMode", "writing-mode"],
		["xmlnsXlink", "xmlns:xlink"],
		["xHeight", "x-height"]
	]), nn = /^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;
	function rn(e) {
		return nn.test("" + e) ? "javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')" : e;
	}
	function an() {}
	var on = null;
	function sn(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var cn = null, ln = null;
	function un(e) {
		var t = xt(e);
		if (t && (e = t.stateNode)) {
			var n = e[ft] || null;
			a: switch (e = t.stateNode, t.type) {
				case "input":
					if (Wt(e, n.value, n.defaultValue, n.defaultValue, n.checked, n.defaultChecked, n.type, n.name), t = n.name, n.type === "radio" && t != null) {
						for (n = e; n.parentNode;) n = n.parentNode;
						for (n = n.querySelectorAll("input[name=\"" + Ut("" + t) + "\"][type=\"radio\"]"), t = 0; t < n.length; t++) {
							var r = n[t];
							if (r !== e && r.form === e.form) {
								var a = r[ft] || null;
								if (!a) throw Error(i(90));
								Wt(r, a.value, a.defaultValue, a.defaultValue, a.checked, a.defaultChecked, a.type, a.name);
							}
						}
						for (t = 0; t < n.length; t++) r = n[t], r.form === e.form && Bt(r);
					}
					break a;
				case "textarea":
					Jt(e, n.value, n.defaultValue);
					break a;
				case "select": t = n.value, t != null && qt(e, !!n.multiple, t, !1);
			}
		}
	}
	var dn = !1;
	function fn(e, t, n) {
		if (dn) return e(t, n);
		dn = !0;
		try {
			return e(t);
		} finally {
			if (dn = !1, (cn !== null || ln !== null) && (bu(), cn && (t = cn, e = ln, ln = cn = null, un(t), e))) for (t = 0; t < e.length; t++) un(e[t]);
		}
	}
	function pn(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var r = n[ft] || null;
		if (r === null) return null;
		n = r[t];
		a: switch (t) {
			case "onClick":
			case "onClickCapture":
			case "onDoubleClick":
			case "onDoubleClickCapture":
			case "onMouseDown":
			case "onMouseDownCapture":
			case "onMouseMove":
			case "onMouseMoveCapture":
			case "onMouseUp":
			case "onMouseUpCapture":
			case "onMouseEnter":
				(r = !r.disabled) || (e = e.type, r = e !== "button" && e !== "input" && e !== "select" && e !== "textarea"), e = !r;
				break a;
			default: e = !1;
		}
		if (e) return null;
		if (n && typeof n != "function") throw Error(i(231, t, typeof n));
		return n;
	}
	var mn = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), hn = !1;
	if (mn) try {
		var gn = {};
		Object.defineProperty(gn, "passive", { get: function() {
			hn = !0;
		} }), window.addEventListener("test", gn, gn), window.removeEventListener("test", gn, gn);
	} catch {
		hn = !1;
	}
	var _n = null, vn = null, yn = null;
	function bn() {
		if (yn) return yn;
		var e, t = vn, n = t.length, r, i = "value" in _n ? _n.value : _n.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return yn = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function xn(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function Sn() {
		return !0;
	}
	function Cn() {
		return !1;
	}
	function wn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? Sn : Cn, this.isPropagationStopped = Cn, this;
		}
		return h(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = Sn);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = Sn);
			},
			persist: function() {},
			isPersistent: Sn
		}), t;
	}
	var Tn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, En = wn(Tn), Dn = h({}, Tn, {
		view: 0,
		detail: 0
	}), On = wn(Dn), kn, An, jn, Mn = h({}, Dn, {
		screenX: 0,
		screenY: 0,
		clientX: 0,
		clientY: 0,
		pageX: 0,
		pageY: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		getModifierState: Hn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== jn && (jn && e.type === "mousemove" ? (kn = e.screenX - jn.screenX, An = e.screenY - jn.screenY) : An = kn = 0, jn = e), kn);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : An;
		}
	}), Nn = wn(Mn), Pn = wn(h({}, Mn, { dataTransfer: 0 })), P = wn(h({}, Dn, { relatedTarget: 0 })), Fn = wn(h({}, Tn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), In = wn(h({}, Tn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Ln = wn(h({}, Tn, { data: 0 })), Rn = {
		Esc: "Escape",
		Spacebar: " ",
		Left: "ArrowLeft",
		Up: "ArrowUp",
		Right: "ArrowRight",
		Down: "ArrowDown",
		Del: "Delete",
		Win: "OS",
		Menu: "ContextMenu",
		Apps: "ContextMenu",
		Scroll: "ScrollLock",
		MozPrintableKey: "Unidentified"
	}, zn = {
		8: "Backspace",
		9: "Tab",
		12: "Clear",
		13: "Enter",
		16: "Shift",
		17: "Control",
		18: "Alt",
		19: "Pause",
		20: "CapsLock",
		27: "Escape",
		32: " ",
		33: "PageUp",
		34: "PageDown",
		35: "End",
		36: "Home",
		37: "ArrowLeft",
		38: "ArrowUp",
		39: "ArrowRight",
		40: "ArrowDown",
		45: "Insert",
		46: "Delete",
		112: "F1",
		113: "F2",
		114: "F3",
		115: "F4",
		116: "F5",
		117: "F6",
		118: "F7",
		119: "F8",
		120: "F9",
		121: "F10",
		122: "F11",
		123: "F12",
		144: "NumLock",
		145: "ScrollLock",
		224: "Meta"
	}, Bn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Vn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Bn[e]) ? !!t[e] : !1;
	}
	function Hn() {
		return Vn;
	}
	var Un = wn(h({}, Dn, {
		key: function(e) {
			if (e.key) {
				var t = Rn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = xn(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? zn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Hn,
		charCode: function(e) {
			return e.type === "keypress" ? xn(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? xn(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), Wn = wn(h({}, Mn, {
		pointerId: 0,
		width: 0,
		height: 0,
		pressure: 0,
		tangentialPressure: 0,
		tiltX: 0,
		tiltY: 0,
		twist: 0,
		pointerType: 0,
		isPrimary: 0
	})), Gn = wn(h({}, Dn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Hn
	})), Kn = wn(h({}, Tn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), F = wn(h({}, Mn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), qn = wn(h({}, Tn, {
		newState: 0,
		oldState: 0
	})), Jn = [
		9,
		13,
		27,
		32
	], Yn = mn && "CompositionEvent" in window, Xn = null;
	mn && "documentMode" in document && (Xn = document.documentMode);
	var Zn = mn && "TextEvent" in window && !Xn, Qn = mn && (!Yn || Xn && 8 < Xn && 11 >= Xn), $n = " ", er = !1;
	function tr(e, t) {
		switch (e) {
			case "keyup": return Jn.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function nr(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var rr = !1;
	function ir(e, t) {
		switch (e) {
			case "compositionend": return nr(t);
			case "keypress": return t.which === 32 ? (er = !0, $n) : null;
			case "textInput": return e = t.data, e === $n && er ? null : e;
			default: return null;
		}
	}
	function ar(e, t) {
		if (rr) return e === "compositionend" || !Yn && tr(e, t) ? (e = bn(), yn = vn = _n = null, rr = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return Qn && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var or = {
		color: !0,
		date: !0,
		datetime: !0,
		"datetime-local": !0,
		email: !0,
		month: !0,
		number: !0,
		password: !0,
		range: !0,
		search: !0,
		tel: !0,
		text: !0,
		time: !0,
		url: !0,
		week: !0
	};
	function sr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!or[e.type] : t === "textarea";
	}
	function cr(e, t, n, r) {
		cn ? ln ? ln.push(r) : ln = [r] : cn = r, t = Ed(t, "onChange"), 0 < t.length && (n = new En("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var lr = null, I = null;
	function ur(e) {
		yd(e, 0);
	}
	function dr(e) {
		if (Bt(St(e))) return e;
	}
	function fr(e, t) {
		if (e === "change") return t;
	}
	var pr = !1;
	if (mn) {
		var mr;
		if (mn) {
			var hr = "oninput" in document;
			if (!hr) {
				var gr = document.createElement("div");
				gr.setAttribute("oninput", "return;"), hr = typeof gr.oninput == "function";
			}
			mr = hr;
		} else mr = !1;
		pr = mr && (!document.documentMode || 9 < document.documentMode);
	}
	function _r() {
		lr && (lr.detachEvent("onpropertychange", vr), I = lr = null);
	}
	function vr(e) {
		if (e.propertyName === "value" && dr(I)) {
			var t = [];
			cr(t, I, e, sn(e)), fn(ur, t);
		}
	}
	function yr(e, t, n) {
		e === "focusin" ? (_r(), lr = t, I = n, lr.attachEvent("onpropertychange", vr)) : e === "focusout" && _r();
	}
	function br(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return dr(I);
	}
	function xr(e, t) {
		if (e === "click") return dr(t);
	}
	function Sr(e, t) {
		if (e === "input" || e === "change") return dr(t);
	}
	function Cr(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var wr = typeof Object.is == "function" ? Object.is : Cr;
	function Tr(e, t) {
		if (wr(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!Te.call(t, i) || !wr(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Er(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Dr(e, t) {
		var n = Er(e);
		e = 0;
		for (var r; n;) {
			if (n.nodeType === 3) {
				if (r = e + n.textContent.length, e <= t && r >= t) return {
					node: n,
					offset: t - e
				};
				e = r;
			}
			a: {
				for (; n;) {
					if (n.nextSibling) {
						n = n.nextSibling;
						break a;
					}
					n = n.parentNode;
				}
				n = void 0;
			}
			n = Er(n);
		}
	}
	function Or(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Or(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function kr(e) {
		e = e != null && e.ownerDocument != null && e.ownerDocument.defaultView != null ? e.ownerDocument.defaultView : window;
		for (var t = Vt(e.document); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = Vt(e.document);
		}
		return t;
	}
	function Ar(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	var jr = mn && "documentMode" in document && 11 >= document.documentMode, Mr = null, Nr = null, Pr = null, Fr = !1;
	function Ir(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Fr || Mr == null || Mr !== Vt(r) || (r = Mr, "selectionStart" in r && Ar(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Pr && Tr(Pr, r) || (Pr = r, r = Ed(Nr, "onSelect"), 0 < r.length && (t = new En("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = Mr)));
	}
	function Lr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Rr = {
		animationend: Lr("Animation", "AnimationEnd"),
		animationiteration: Lr("Animation", "AnimationIteration"),
		animationstart: Lr("Animation", "AnimationStart"),
		transitionrun: Lr("Transition", "TransitionRun"),
		transitionstart: Lr("Transition", "TransitionStart"),
		transitioncancel: Lr("Transition", "TransitionCancel"),
		transitionend: Lr("Transition", "TransitionEnd")
	}, zr = {}, Br = {};
	mn && (Br = document.createElement("div").style, "AnimationEvent" in window || (delete Rr.animationend.animation, delete Rr.animationiteration.animation, delete Rr.animationstart.animation), "TransitionEvent" in window || delete Rr.transitionend.transition);
	function Vr(e) {
		if (zr[e]) return zr[e];
		if (!Rr[e]) return e;
		var t = Rr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in Br) return zr[e] = t[n];
		return e;
	}
	var Hr = Vr("animationend"), Ur = Vr("animationiteration"), Wr = Vr("animationstart"), Gr = Vr("transitionrun"), Kr = Vr("transitionstart"), qr = Vr("transitioncancel"), Jr = Vr("transitionend"), Yr = /* @__PURE__ */ new Map(), Xr = "abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	Xr.push("scrollEnd");
	function Zr(e, t) {
		Yr.set(e, t), Dt(t, [e]);
	}
	var Qr = typeof reportError == "function" ? reportError : function(e) {
		if (typeof window == "object" && typeof window.ErrorEvent == "function") {
			var t = new window.ErrorEvent("error", {
				bubbles: !0,
				cancelable: !0,
				message: typeof e == "object" && e && typeof e.message == "string" ? String(e.message) : String(e),
				error: e
			});
			if (!window.dispatchEvent(t)) return;
		}
		console.error(e);
	}, $r = [], ei = 0, ti = 0;
	function ni() {
		for (var e = ei, t = ti = ei = 0; t < e;) {
			var n = $r[t];
			$r[t++] = null;
			var r = $r[t];
			$r[t++] = null;
			var i = $r[t];
			$r[t++] = null;
			var a = $r[t];
			if ($r[t++] = null, r !== null && i !== null) {
				var o = r.pending;
				o === null ? i.next = i : (i.next = o.next, o.next = i), r.pending = i;
			}
			a !== 0 && oi(n, i, a);
		}
	}
	function ri(e, t, n, r) {
		$r[ei++] = e, $r[ei++] = t, $r[ei++] = n, $r[ei++] = r, ti |= r, e.lanes |= r, e = e.alternate, e !== null && (e.lanes |= r);
	}
	function ii(e, t, n, r) {
		return ri(e, t, n, r), si(e);
	}
	function ai(e, t) {
		return ri(e, null, null, t), si(e);
	}
	function oi(e, t, n) {
		e.lanes |= n;
		var r = e.alternate;
		r !== null && (r.lanes |= n);
		for (var i = !1, a = e.return; a !== null;) a.childLanes |= n, r = a.alternate, r !== null && (r.childLanes |= n), a.tag === 22 && (e = a.stateNode, e === null || e._visibility & 1 || (i = !0)), e = a, a = a.return;
		return e.tag === 3 ? (a = e.stateNode, i && t !== null && (i = 31 - He(n), e = a.hiddenUpdates, r = e[i], r === null ? e[i] = [t] : r.push(t), t.lane = n | 536870912), a) : null;
	}
	function si(e) {
		if (50 < du) throw du = 0, fu = null, Error(i(185));
		for (var t = e.return; t !== null;) e = t, t = e.return;
		return e.tag === 3 ? e.stateNode : null;
	}
	var ci = {};
	function li(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.refCleanup = this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function ui(e, t, n, r) {
		return new li(e, t, n, r);
	}
	function di(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function fi(e, t) {
		var n = e.alternate;
		return n === null ? (n = ui(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 65011712, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n.refCleanup = e.refCleanup, n;
	}
	function pi(e, t) {
		e.flags &= 65011714;
		var n = e.alternate;
		return n === null ? (e.childLanes = 0, e.lanes = t, e.child = null, e.subtreeFlags = 0, e.memoizedProps = null, e.memoizedState = null, e.updateQueue = null, e.dependencies = null, e.stateNode = null) : (e.childLanes = n.childLanes, e.lanes = n.lanes, e.child = n.child, e.subtreeFlags = 0, e.deletions = null, e.memoizedProps = n.memoizedProps, e.memoizedState = n.memoizedState, e.updateQueue = n.updateQueue, e.type = n.type, t = n.dependencies, e.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}), e;
	}
	function mi(e, t, n, r, a, o) {
		var s = 0;
		if (r = e, typeof e == "function") di(e) && (s = 1);
		else if (typeof e == "string") s = Uf(e, n, ue.current) ? 26 : e === "html" || e === "head" || e === "body" ? 27 : 5;
		else a: switch (e) {
			case k: return e = ui(31, n, t, a), e.elementType = k, e.lanes = o, e;
			case y: return hi(n.children, a, o, t);
			case b:
				s = 8, a |= 24;
				break;
			case x: return e = ui(12, n, t, a | 2), e.elementType = x, e.lanes = o, e;
			case T: return e = ui(13, n, t, a), e.elementType = T, e.lanes = o, e;
			case E: return e = ui(19, n, t, a), e.elementType = E, e.lanes = o, e;
			default:
				if (typeof e == "object" && e) switch (e.$$typeof) {
					case C:
						s = 10;
						break a;
					case S:
						s = 9;
						break a;
					case w:
						s = 11;
						break a;
					case D:
						s = 14;
						break a;
					case O:
						s = 16, r = null;
						break a;
				}
				s = 29, n = Error(i(130, e === null ? "null" : typeof e, "")), r = null;
		}
		return t = ui(s, n, t, a), t.elementType = e, t.type = r, t.lanes = o, t;
	}
	function hi(e, t, n, r) {
		return e = ui(7, e, r, t), e.lanes = n, e;
	}
	function gi(e, t, n) {
		return e = ui(6, e, null, t), e.lanes = n, e;
	}
	function _i(e) {
		var t = ui(18, null, null, 0);
		return t.stateNode = e, t;
	}
	function vi(e, t, n) {
		return t = ui(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	var yi = /* @__PURE__ */ new WeakMap();
	function bi(e, t) {
		if (typeof e == "object" && e) {
			var n = yi.get(e);
			return n === void 0 ? (t = {
				value: e,
				source: t,
				stack: we(t)
			}, yi.set(e, t), t) : n;
		}
		return {
			value: e,
			source: t,
			stack: we(t)
		};
	}
	var xi = [], Si = 0, Ci = null, wi = 0, Ti = [], Ei = 0, Di = null, Oi = 1, ki = "";
	function Ai(e, t) {
		xi[Si++] = wi, xi[Si++] = Ci, Ci = e, wi = t;
	}
	function ji(e, t, n) {
		Ti[Ei++] = Oi, Ti[Ei++] = ki, Ti[Ei++] = Di, Di = e;
		var r = Oi;
		e = ki;
		var i = 32 - He(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - He(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, Oi = 1 << 32 - He(t) + i | n << i | r, ki = a + e;
		} else Oi = 1 << a | n << i | r, ki = e;
	}
	function Mi(e) {
		e.return !== null && (Ai(e, 1), ji(e, 1, 0));
	}
	function Ni(e) {
		for (; e === Ci;) Ci = xi[--Si], xi[Si] = null, wi = xi[--Si], xi[Si] = null;
		for (; e === Di;) Di = Ti[--Ei], Ti[Ei] = null, ki = Ti[--Ei], Ti[Ei] = null, Oi = Ti[--Ei], Ti[Ei] = null;
	}
	function Pi(e, t) {
		Ti[Ei++] = Oi, Ti[Ei++] = ki, Ti[Ei++] = Di, Oi = t.id, ki = t.overflow, Di = e;
	}
	var Fi = null, L = null, R = !1, Ii = null, Li = !1, Ri = Error(i(519));
	function zi(e) {
		throw Gi(bi(Error(i(418, 1 < arguments.length && arguments[1] !== void 0 && arguments[1] ? "text" : "HTML", "")), e)), Ri;
	}
	function Bi(e) {
		var t = e.stateNode, n = e.type, r = e.memoizedProps;
		switch (t[dt] = e, t[ft] = r, n) {
			case "dialog":
				Q("cancel", t), Q("close", t);
				break;
			case "iframe":
			case "object":
			case "embed":
				Q("load", t);
				break;
			case "video":
			case "audio":
				for (n = 0; n < _d.length; n++) Q(_d[n], t);
				break;
			case "source":
				Q("error", t);
				break;
			case "img":
			case "image":
			case "link":
				Q("error", t), Q("load", t);
				break;
			case "details":
				Q("toggle", t);
				break;
			case "input":
				Q("invalid", t), Gt(t, r.value, r.defaultValue, r.checked, r.defaultChecked, r.type, r.name, !0);
				break;
			case "select":
				Q("invalid", t);
				break;
			case "textarea": Q("invalid", t), Yt(t, r.value, r.defaultValue, r.children);
		}
		n = r.children, typeof n != "string" && typeof n != "number" && typeof n != "bigint" || t.textContent === "" + n || !0 === r.suppressHydrationWarning || Md(t.textContent, n) ? (r.popover != null && (Q("beforetoggle", t), Q("toggle", t)), r.onScroll != null && Q("scroll", t), r.onScrollEnd != null && Q("scrollend", t), r.onClick != null && (t.onclick = an), t = !0) : t = !1, t || zi(e, !0);
	}
	function Vi(e) {
		for (Fi = e.return; Fi;) switch (Fi.tag) {
			case 5:
			case 31:
			case 13:
				Li = !1;
				return;
			case 27:
			case 3:
				Li = !0;
				return;
			default: Fi = Fi.return;
		}
	}
	function Hi(e) {
		if (e !== Fi) return !1;
		if (!R) return Vi(e), R = !0, !1;
		var t = e.tag, n;
		if ((n = t !== 3 && t !== 27) && ((n = t === 5) && (n = e.type, n = n === "form" || n === "button" || Ud(e.type, e.memoizedProps)), n = !n), n && L && zi(e), Vi(e), t === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			L = uf(e);
		} else if (t === 31) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			L = uf(e);
		} else t === 27 ? (t = L, Zd(e.type) ? (e = lf, lf = null, L = e) : L = t) : L = Fi ? cf(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Ui() {
		L = Fi = null, R = !1;
	}
	function Wi() {
		var e = Ii;
		return e !== null && (Zl === null ? Zl = e : Zl.push.apply(Zl, e), Ii = null), e;
	}
	function Gi(e) {
		Ii === null ? Ii = [e] : Ii.push(e);
	}
	var Ki = ce(null), qi = null, Ji = null;
	function Yi(e, t, n) {
		N(Ki, t._currentValue), t._currentValue = n;
	}
	function Xi(e) {
		e._currentValue = Ki.current, le(Ki);
	}
	function Zi(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function Qi(e, t, n, r) {
		var a = e.child;
		for (a !== null && (a.return = e); a !== null;) {
			var o = a.dependencies;
			if (o !== null) {
				var s = a.child;
				o = o.firstContext;
				a: for (; o !== null;) {
					var c = o;
					o = a;
					for (var l = 0; l < t.length; l++) if (c.context === t[l]) {
						o.lanes |= n, c = o.alternate, c !== null && (c.lanes |= n), Zi(o.return, n, e), r || (s = null);
						break a;
					}
					o = c.next;
				}
			} else if (a.tag === 18) {
				if (s = a.return, s === null) throw Error(i(341));
				s.lanes |= n, o = s.alternate, o !== null && (o.lanes |= n), Zi(s, n, e), s = null;
			} else s = a.child;
			if (s !== null) s.return = a;
			else for (s = a; s !== null;) {
				if (s === e) {
					s = null;
					break;
				}
				if (a = s.sibling, a !== null) {
					a.return = s.return, s = a;
					break;
				}
				s = s.return;
			}
			a = s;
		}
	}
	function $i(e, t, n, r) {
		e = null;
		for (var a = t, o = !1; a !== null;) {
			if (!o) {
				if (a.flags & 524288) o = !0;
				else if (a.flags & 262144) break;
			}
			if (a.tag === 10) {
				var s = a.alternate;
				if (s === null) throw Error(i(387));
				if (s = s.memoizedProps, s !== null) {
					var c = a.type;
					wr(a.pendingProps.value, s.value) || (e === null ? e = [c] : e.push(c));
				}
			} else if (a === pe.current) {
				if (s = a.alternate, s === null) throw Error(i(387));
				s.memoizedState.memoizedState !== a.memoizedState.memoizedState && (e === null ? e = [Qf] : e.push(Qf));
			}
			a = a.return;
		}
		e !== null && Qi(t, e, n, r), t.flags |= 262144;
	}
	function ea(e) {
		for (e = e.firstContext; e !== null;) {
			if (!wr(e.context._currentValue, e.memoizedValue)) return !0;
			e = e.next;
		}
		return !1;
	}
	function ta(e) {
		qi = e, Ji = null, e = e.dependencies, e !== null && (e.firstContext = null);
	}
	function z(e) {
		return ra(qi, e);
	}
	function na(e, t) {
		return qi === null && ta(e), ra(e, t);
	}
	function ra(e, t) {
		var n = t._currentValue;
		if (t = {
			context: t,
			memoizedValue: n,
			next: null
		}, Ji === null) {
			if (e === null) throw Error(i(308));
			Ji = t, e.dependencies = {
				lanes: 0,
				firstContext: t
			}, e.flags |= 524288;
		} else Ji = Ji.next = t;
		return n;
	}
	var ia = typeof AbortController < "u" ? AbortController : function() {
		var e = [], t = this.signal = {
			aborted: !1,
			addEventListener: function(t, n) {
				e.push(n);
			}
		};
		this.abort = function() {
			t.aborted = !0, e.forEach(function(e) {
				return e();
			});
		};
	}, aa = t.unstable_scheduleCallback, oa = t.unstable_NormalPriority, sa = {
		$$typeof: C,
		Consumer: null,
		Provider: null,
		_currentValue: null,
		_currentValue2: null,
		_threadCount: 0
	};
	function B() {
		return {
			controller: new ia(),
			data: /* @__PURE__ */ new Map(),
			refCount: 0
		};
	}
	function ca(e) {
		e.refCount--, e.refCount === 0 && aa(oa, function() {
			e.controller.abort();
		});
	}
	var la = null, ua = 0, da = 0, fa = null;
	function pa(e, t) {
		if (la === null) {
			var n = la = [];
			ua = 0, da = dd(), fa = {
				status: "pending",
				value: void 0,
				then: function(e) {
					n.push(e);
				}
			};
		}
		return ua++, t.then(ma, ma), t;
	}
	function ma() {
		if (--ua === 0 && la !== null) {
			fa !== null && (fa.status = "fulfilled");
			var e = la;
			la = null, da = 0, fa = null;
			for (var t = 0; t < e.length; t++) (0, e[t])();
		}
	}
	function ha(e, t) {
		var n = [], r = {
			status: "pending",
			value: null,
			reason: null,
			then: function(e) {
				n.push(e);
			}
		};
		return e.then(function() {
			r.status = "fulfilled", r.value = t;
			for (var e = 0; e < n.length; e++) (0, n[e])(t);
		}, function(e) {
			for (r.status = "rejected", r.reason = e, e = 0; e < n.length; e++) (0, n[e])(void 0);
		}), r;
	}
	var V = j.S;
	j.S = function(e, t) {
		eu = Ae(), typeof t == "object" && t && typeof t.then == "function" && pa(e, t), V !== null && V(e, t);
	};
	var ga = ce(null);
	function _a() {
		var e = ga.current;
		return e === null ? Rl.pooledCache : e;
	}
	function H(e, t) {
		t === null ? N(ga, ga.current) : N(ga, t.pool);
	}
	function va() {
		var e = _a();
		return e === null ? null : {
			parent: sa._currentValue,
			pool: e
		};
	}
	var ya = Error(i(460)), U = Error(i(474)), W = Error(i(542)), ba = { then: function() {} };
	function xa(e) {
		return e = e.status, e === "fulfilled" || e === "rejected";
	}
	function Sa(e, t, n) {
		switch (n = e[n], n === void 0 ? e.push(t) : n !== t && (t.then(an, an), t = n), t.status) {
			case "fulfilled": return t.value;
			case "rejected": throw e = t.reason, Ea(e), e;
			default:
				if (typeof t.status == "string") t.then(an, an);
				else {
					if (e = Rl, e !== null && 100 < e.shellSuspendCounter) throw Error(i(482));
					e = t, e.status = "pending", e.then(function(e) {
						if (t.status === "pending") {
							var n = t;
							n.status = "fulfilled", n.value = e;
						}
					}, function(e) {
						if (t.status === "pending") {
							var n = t;
							n.status = "rejected", n.reason = e;
						}
					});
				}
				switch (t.status) {
					case "fulfilled": return t.value;
					case "rejected": throw e = t.reason, Ea(e), e;
				}
				throw wa = t, ya;
		}
	}
	function Ca(e) {
		try {
			var t = e._init;
			return t(e._payload);
		} catch (e) {
			throw typeof e == "object" && e && typeof e.then == "function" ? (wa = e, ya) : e;
		}
	}
	var wa = null;
	function Ta() {
		if (wa === null) throw Error(i(459));
		var e = wa;
		return wa = null, e;
	}
	function Ea(e) {
		if (e === ya || e === W) throw Error(i(483));
	}
	var Da = null, Oa = 0;
	function ka(e) {
		var t = Oa;
		return Oa += 1, Da === null && (Da = []), Sa(Da, e, t);
	}
	function Aa(e, t) {
		t = t.props.ref, e.ref = t === void 0 ? null : t;
	}
	function ja(e, t) {
		throw t.$$typeof === g ? Error(i(525)) : (e = Object.prototype.toString.call(t), Error(i(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e)));
	}
	function Ma(e) {
		function t(t, n) {
			if (e) {
				var r = t.deletions;
				r === null ? (t.deletions = [n], t.flags |= 16) : r.push(n);
			}
		}
		function n(n, r) {
			if (!e) return null;
			for (; r !== null;) t(n, r), r = r.sibling;
			return null;
		}
		function r(e) {
			for (var t = /* @__PURE__ */ new Map(); e !== null;) e.key === null ? t.set(e.index, e) : t.set(e.key, e), e = e.sibling;
			return t;
		}
		function a(e, t) {
			return e = fi(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 67108866, n) : (r = r.index, r < n ? (t.flags |= 67108866, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 67108866), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = gi(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === y ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === O && Ca(i) === t.type) ? (t = a(t, n.props), Aa(t, n), t.return = e, t) : (t = mi(n.type, n.key, n.props, null, e.mode, r), Aa(t, n), t.return = e, t);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = vi(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = hi(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number" || typeof t == "bigint") return t = gi("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case _: return n = mi(t.type, t.key, t.props, null, e.mode, n), Aa(n, t), n.return = e, n;
					case v: return t = vi(t, e.mode, n), t.return = e, t;
					case O: return t = Ca(t), f(e, t, n);
				}
				if (A(t) || ne(t)) return t = hi(t, e.mode, n, null), t.return = e, t;
				if (typeof t.then == "function") return f(e, ka(t), n);
				if (t.$$typeof === C) return f(e, na(e, t), n);
				ja(e, t);
			}
			return null;
		}
		function p(e, t, n, r) {
			var i = t === null ? null : t.key;
			if (typeof n == "string" && n !== "" || typeof n == "number" || typeof n == "bigint") return i === null ? c(e, t, "" + n, r) : null;
			if (typeof n == "object" && n) {
				switch (n.$$typeof) {
					case _: return n.key === i ? l(e, t, n, r) : null;
					case v: return n.key === i ? u(e, t, n, r) : null;
					case O: return n = Ca(n), p(e, t, n, r);
				}
				if (A(n) || ne(n)) return i === null ? d(e, t, n, r, null) : null;
				if (typeof n.then == "function") return p(e, t, ka(n), r);
				if (n.$$typeof === C) return p(e, t, na(e, n), r);
				ja(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number" || typeof r == "bigint") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case _: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case v: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case O: return r = Ca(r), m(e, t, n, r, i);
				}
				if (A(r) || ne(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				if (typeof r.then == "function") return m(e, t, n, ka(r), i);
				if (r.$$typeof === C) return m(e, t, n, na(t, r), i);
				ja(t, r);
			}
			return null;
		}
		function h(i, a, s, c) {
			for (var l = null, u = null, d = a, h = a = 0, g = null; d !== null && h < s.length; h++) {
				d.index > h ? (g = d, d = null) : g = d.sibling;
				var _ = p(i, d, s[h], c);
				if (_ === null) {
					d === null && (d = g);
					break;
				}
				e && d && _.alternate === null && t(i, d), a = o(_, a, h), u === null ? l = _ : u.sibling = _, u = _, d = g;
			}
			if (h === s.length) return n(i, d), R && Ai(i, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(i, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return R && Ai(i, h), l;
			}
			for (d = r(d); h < s.length; h++) g = m(d, i, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(i, e);
			}), R && Ai(i, h), l;
		}
		function g(a, s, c, l) {
			if (c == null) throw Error(i(151));
			for (var u = null, d = null, h = s, g = s = 0, _ = null, v = c.next(); h !== null && !v.done; g++, v = c.next()) {
				h.index > g ? (_ = h, h = null) : _ = h.sibling;
				var y = p(a, h, v.value, l);
				if (y === null) {
					h === null && (h = _);
					break;
				}
				e && h && y.alternate === null && t(a, h), s = o(y, s, g), d === null ? u = y : d.sibling = y, d = y, h = _;
			}
			if (v.done) return n(a, h), R && Ai(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return R && Ai(a, g), u;
			}
			for (h = r(h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), R && Ai(a, g), u;
		}
		function b(e, r, o, c) {
			if (typeof o == "object" && o && o.type === y && o.key === null && (o = o.props.children), typeof o == "object" && o) {
				switch (o.$$typeof) {
					case _:
						a: {
							for (var l = o.key; r !== null;) {
								if (r.key === l) {
									if (l = o.type, l === y) {
										if (r.tag === 7) {
											n(e, r.sibling), c = a(r, o.props.children), c.return = e, e = c;
											break a;
										}
									} else if (r.elementType === l || typeof l == "object" && l && l.$$typeof === O && Ca(l) === r.type) {
										n(e, r.sibling), c = a(r, o.props), Aa(c, o), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							o.type === y ? (c = hi(o.props.children, e.mode, c, o.key), c.return = e, e = c) : (c = mi(o.type, o.key, o.props, null, e.mode, c), Aa(c, o), c.return = e, e = c);
						}
						return s(e);
					case v:
						a: {
							for (l = o.key; r !== null;) {
								if (r.key === l) {
									if (r.tag === 4 && r.stateNode.containerInfo === o.containerInfo && r.stateNode.implementation === o.implementation) {
										n(e, r.sibling), c = a(r, o.children || []), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							c = vi(o, e.mode, c), c.return = e, e = c;
						}
						return s(e);
					case O: return o = Ca(o), b(e, r, o, c);
				}
				if (A(o)) return h(e, r, o, c);
				if (ne(o)) {
					if (l = ne(o), typeof l != "function") throw Error(i(150));
					return o = l.call(o), g(e, r, o, c);
				}
				if (typeof o.then == "function") return b(e, r, ka(o), c);
				if (o.$$typeof === C) return b(e, r, na(e, o), c);
				ja(e, o);
			}
			return typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint" ? (o = "" + o, r !== null && r.tag === 6 ? (n(e, r.sibling), c = a(r, o), c.return = e, e = c) : (n(e, r), c = gi(o, e.mode, c), c.return = e, e = c), s(e)) : n(e, r);
		}
		return function(e, t, n, r) {
			try {
				Oa = 0;
				var i = b(e, t, n, r);
				return Da = null, i;
			} catch (t) {
				if (t === ya || t === W) throw t;
				var a = ui(29, t, null, e.mode);
				return a.lanes = r, a.return = e, a;
			}
		};
	}
	var Na = Ma(!0), Pa = Ma(!1), Fa = !1;
	function Ia(e) {
		e.updateQueue = {
			baseState: e.memoizedState,
			firstBaseUpdate: null,
			lastBaseUpdate: null,
			shared: {
				pending: null,
				lanes: 0,
				hiddenCallbacks: null
			},
			callbacks: null
		};
	}
	function La(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			callbacks: null
		});
	}
	function Ra(e) {
		return {
			lane: e,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function za(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, q & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, t = si(e), oi(e, null, n), t;
		}
		return ri(e, r, t, n), si(e);
	}
	function Ba(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194048)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, it(e, n);
		}
	}
	function Va(e, t) {
		var n = e.updateQueue, r = e.alternate;
		if (r !== null && (r = r.updateQueue, n === r)) {
			var i = null, a = null;
			if (n = n.firstBaseUpdate, n !== null) {
				do {
					var o = {
						lane: n.lane,
						tag: n.tag,
						payload: n.payload,
						callback: null,
						next: null
					};
					a === null ? i = a = o : a = a.next = o, n = n.next;
				} while (n !== null);
				a === null ? i = a = t : a = a.next = t;
			} else i = a = t;
			n = {
				baseState: r.baseState,
				firstBaseUpdate: i,
				lastBaseUpdate: a,
				shared: r.shared,
				callbacks: r.callbacks
			}, e.updateQueue = n;
			return;
		}
		e = n.lastBaseUpdate, e === null ? n.firstBaseUpdate = t : e.next = t, n.lastBaseUpdate = t;
	}
	var Ha = !1;
	function Ua() {
		if (Ha) {
			var e = fa;
			if (e !== null) throw e;
		}
	}
	function Wa(e, t, n, r) {
		Ha = !1;
		var i = e.updateQueue;
		Fa = !1;
		var a = i.firstBaseUpdate, o = i.lastBaseUpdate, s = i.shared.pending;
		if (s !== null) {
			i.shared.pending = null;
			var c = s, l = c.next;
			c.next = null, o === null ? a = l : o.next = l, o = c;
			var u = e.alternate;
			u !== null && (u = u.updateQueue, s = u.lastBaseUpdate, s !== o && (s === null ? u.firstBaseUpdate = l : s.next = l, u.lastBaseUpdate = c));
		}
		if (a !== null) {
			var d = i.baseState;
			o = 0, u = l = c = null, s = a;
			do {
				var f = s.lane & -536870913, p = f !== s.lane;
				if (p ? (Y & f) === f : (r & f) === f) {
					f !== 0 && f === da && (Ha = !0), u !== null && (u = u.next = {
						lane: 0,
						tag: s.tag,
						payload: s.payload,
						callback: null,
						next: null
					});
					a: {
						var m = e, g = s;
						f = t;
						var _ = n;
						switch (g.tag) {
							case 1:
								if (m = g.payload, typeof m == "function") {
									d = m.call(_, d, f);
									break a;
								}
								d = m;
								break a;
							case 3: m.flags = m.flags & -65537 | 128;
							case 0:
								if (m = g.payload, f = typeof m == "function" ? m.call(_, d, f) : m, f == null) break a;
								d = h({}, d, f);
								break a;
							case 2: Fa = !0;
						}
					}
					f = s.callback, f !== null && (e.flags |= 64, p && (e.flags |= 8192), p = i.callbacks, p === null ? i.callbacks = [f] : p.push(f));
				} else p = {
					lane: f,
					tag: s.tag,
					payload: s.payload,
					callback: s.callback,
					next: null
				}, u === null ? (l = u = p, c = d) : u = u.next = p, o |= f;
				if (s = s.next, s === null) {
					if (s = i.shared.pending, s === null) break;
					p = s, s = p.next, p.next = null, i.lastBaseUpdate = p, i.shared.pending = null;
				}
			} while (1);
			u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, a === null && (i.shared.lanes = 0), Gl |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function Ga(e, t) {
		if (typeof e != "function") throw Error(i(191, e));
		e.call(t);
	}
	function Ka(e, t) {
		var n = e.callbacks;
		if (n !== null) for (e.callbacks = null, e = 0; e < n.length; e++) Ga(n[e], t);
	}
	var qa = ce(null), Ja = ce(0);
	function Ya(e, t) {
		e = Ul, N(Ja, e), N(qa, t), Ul = e | t.baseLanes;
	}
	function Xa() {
		N(Ja, Ul), N(qa, qa.current);
	}
	function Za() {
		Ul = Ja.current, le(qa), le(Ja);
	}
	var Qa = ce(null), $a = null;
	function eo(e) {
		var t = e.alternate;
		N(ao, ao.current & 1), N(Qa, e), $a === null && (t === null || qa.current !== null || t.memoizedState !== null) && ($a = e);
	}
	function to(e) {
		N(ao, ao.current), N(Qa, e), $a === null && ($a = e);
	}
	function no(e) {
		e.tag === 22 ? (N(ao, ao.current), N(Qa, e), $a === null && ($a = e)) : ro(e);
	}
	function ro() {
		N(ao, ao.current), N(Qa, Qa.current);
	}
	function io(e) {
		le(Qa), $a === e && ($a = null), le(ao);
	}
	var ao = ce(0);
	function oo(e) {
		for (var t = e; t !== null;) {
			if (t.tag === 13) {
				var n = t.memoizedState;
				if (n !== null && (n = n.dehydrated, n === null || af(n) || of(n))) return t;
			} else if (t.tag === 19 && (t.memoizedProps.revealOrder === "forwards" || t.memoizedProps.revealOrder === "backwards" || t.memoizedProps.revealOrder === "unstable_legacy-backwards" || t.memoizedProps.revealOrder === "together")) {
				if (t.flags & 128) return t;
			} else if (t.child !== null) {
				t.child.return = t, t = t.child;
				continue;
			}
			if (t === e) break;
			for (; t.sibling === null;) {
				if (t.return === null || t.return === e) return null;
				t = t.return;
			}
			t.sibling.return = t.return, t = t.sibling;
		}
		return null;
	}
	var so = 0, G = null, K = null, co = null, lo = !1, uo = !1, fo = !1, po = 0, mo = 0, ho = null, go = 0;
	function _o() {
		throw Error(i(321));
	}
	function vo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!wr(e[n], t[n])) return !1;
		return !0;
	}
	function yo(e, t, n, r, i, a) {
		return so = a, G = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, j.H = e === null || e.memoizedState === null ? Is : Ls, fo = !1, a = n(r, i), fo = !1, uo && (a = xo(t, n, r, i)), bo(e), a;
	}
	function bo(e) {
		j.H = Fs;
		var t = K !== null && K.next !== null;
		if (so = 0, co = K = G = null, lo = !1, mo = 0, ho = null, t) throw Error(i(300));
		e === null || ec || (e = e.dependencies, e !== null && ea(e) && (ec = !0));
	}
	function xo(e, t, n, r) {
		G = e;
		var a = 0;
		do {
			if (uo && (ho = null), mo = 0, uo = !1, 25 <= a) throw Error(i(301));
			if (a += 1, co = K = null, e.updateQueue != null) {
				var o = e.updateQueue;
				o.lastEffect = null, o.events = null, o.stores = null, o.memoCache != null && (o.memoCache.index = 0);
			}
			j.H = Rs, o = t(n, r);
		} while (uo);
		return o;
	}
	function So() {
		var e = j.H, t = e.useState()[0];
		return t = typeof t.then == "function" ? ko(t) : t, e = e.useState()[0], (K === null ? null : K.memoizedState) !== e && (G.flags |= 1024), t;
	}
	function Co() {
		var e = po !== 0;
		return po = 0, e;
	}
	function wo(e, t, n) {
		t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~n;
	}
	function To(e) {
		if (lo) {
			for (e = e.memoizedState; e !== null;) {
				var t = e.queue;
				t !== null && (t.pending = null), e = e.next;
			}
			lo = !1;
		}
		so = 0, co = K = G = null, uo = !1, mo = po = 0, ho = null;
	}
	function Eo() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return co === null ? G.memoizedState = co = e : co = co.next = e, co;
	}
	function Do() {
		if (K === null) {
			var e = G.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = K.next;
		var t = co === null ? G.memoizedState : co.next;
		if (t !== null) co = t, K = e;
		else {
			if (e === null) throw G.alternate === null ? Error(i(467)) : Error(i(310));
			K = e, e = {
				memoizedState: K.memoizedState,
				baseState: K.baseState,
				baseQueue: K.baseQueue,
				queue: K.queue,
				next: null
			}, co === null ? G.memoizedState = co = e : co = co.next = e;
		}
		return co;
	}
	function Oo() {
		return {
			lastEffect: null,
			events: null,
			stores: null,
			memoCache: null
		};
	}
	function ko(e) {
		var t = mo;
		return mo += 1, ho === null && (ho = []), e = Sa(ho, e, t), t = G, (co === null ? t.memoizedState : co.next) === null && (t = t.alternate, j.H = t === null || t.memoizedState === null ? Is : Ls), e;
	}
	function Ao(e) {
		if (typeof e == "object" && e) {
			if (typeof e.then == "function") return ko(e);
			if (e.$$typeof === C) return z(e);
		}
		throw Error(i(438, String(e)));
	}
	function jo(e) {
		var t = null, n = G.updateQueue;
		if (n !== null && (t = n.memoCache), t == null) {
			var r = G.alternate;
			r !== null && (r = r.updateQueue, r !== null && (r = r.memoCache, r != null && (t = {
				data: r.data.map(function(e) {
					return e.slice();
				}),
				index: 0
			})));
		}
		if (t ?? (t = {
			data: [],
			index: 0
		}), n === null && (n = Oo(), G.updateQueue = n), n.memoCache = t, n = t.data[t.index], n === void 0) for (n = t.data[t.index] = Array(e), r = 0; r < e; r++) n[r] = ee;
		return t.index++, n;
	}
	function Mo(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function No(e) {
		return Po(Do(), K, e);
	}
	function Po(e, t, n) {
		var r = e.queue;
		if (r === null) throw Error(i(311));
		r.lastRenderedReducer = n;
		var a = e.baseQueue, o = r.pending;
		if (o !== null) {
			if (a !== null) {
				var s = a.next;
				a.next = o.next, o.next = s;
			}
			t.baseQueue = a = o, r.pending = null;
		}
		if (o = e.baseState, a === null) e.memoizedState = o;
		else {
			t = a.next;
			var c = s = null, l = null, u = t, d = !1;
			do {
				var f = u.lane & -536870913;
				if (f === u.lane ? (so & f) === f : (Y & f) === f) {
					var p = u.revertLane;
					if (p === 0) l !== null && (l = l.next = {
						lane: 0,
						revertLane: 0,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}), f === da && (d = !0);
					else if ((so & p) === p) {
						u = u.next, p === da && (d = !0);
						continue;
					} else f = {
						lane: 0,
						revertLane: u.revertLane,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}, l === null ? (c = l = f, s = o) : l = l.next = f, G.lanes |= p, Gl |= p;
					f = u.action, fo && n(o, f), o = u.hasEagerState ? u.eagerState : n(o, f);
				} else p = {
					lane: f,
					revertLane: u.revertLane,
					gesture: u.gesture,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}, l === null ? (c = l = p, s = o) : l = l.next = p, G.lanes |= f, Gl |= f;
				u = u.next;
			} while (u !== null && u !== t);
			if (l === null ? s = o : l.next = c, !wr(o, e.memoizedState) && (ec = !0, d && (n = fa, n !== null))) throw n;
			e.memoizedState = o, e.baseState = s, e.baseQueue = l, r.lastRenderedState = o;
		}
		return a === null && (r.lanes = 0), [e.memoizedState, r.dispatch];
	}
	function Fo(e) {
		var t = Do(), n = t.queue;
		if (n === null) throw Error(i(311));
		n.lastRenderedReducer = e;
		var r = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			wr(o, t.memoizedState) || (ec = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, r];
	}
	function Io(e, t, n) {
		var r = G, a = Do(), o = R;
		if (o) {
			if (n === void 0) throw Error(i(407));
			n = n();
		} else n = t();
		var s = !wr((K || a).memoizedState, n);
		if (s && (a.memoizedState = n, ec = !0), a = a.queue, ss(zo.bind(null, r, a, e), [e]), a.getSnapshot !== t || s || co !== null && co.memoizedState.tag & 1) {
			if (r.flags |= 2048, ns(9, { destroy: void 0 }, Ro.bind(null, r, a, n, t), null), Rl === null) throw Error(i(349));
			o || so & 127 || Lo(r, t, n);
		}
		return n;
	}
	function Lo(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = G.updateQueue, t === null ? (t = Oo(), G.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function Ro(e, t, n, r) {
		t.value = n, t.getSnapshot = r, Bo(t) && Vo(e);
	}
	function zo(e, t, n) {
		return n(function() {
			Bo(t) && Vo(e);
		});
	}
	function Bo(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !wr(e, n);
		} catch {
			return !0;
		}
	}
	function Vo(e) {
		var t = ai(e, 2);
		t !== null && hu(t, e, 2);
	}
	function Ho(e) {
		var t = Eo();
		if (typeof e == "function") {
			var n = e;
			if (e = n(), fo) {
				Ve(!0);
				try {
					n();
				} finally {
					Ve(!1);
				}
			}
		}
		return t.memoizedState = t.baseState = e, t.queue = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Mo,
			lastRenderedState: e
		}, t;
	}
	function Uo(e, t, n, r) {
		return e.baseState = n, Po(e, K, typeof r == "function" ? r : Mo);
	}
	function Wo(e, t, n, r, a) {
		if (Ms(e)) throw Error(i(485));
		if (e = t.action, e !== null) {
			var o = {
				payload: a,
				action: e,
				next: null,
				isTransition: !0,
				status: "pending",
				value: null,
				reason: null,
				listeners: [],
				then: function(e) {
					o.listeners.push(e);
				}
			};
			j.T === null ? o.isTransition = !1 : n(!0), r(o), n = t.pending, n === null ? (o.next = t.pending = o, Go(t, o)) : (o.next = n.next, t.pending = n.next = o);
		}
	}
	function Go(e, t) {
		var n = t.action, r = t.payload, i = e.state;
		if (t.isTransition) {
			var a = j.T, o = {};
			j.T = o;
			try {
				var s = n(i, r), c = j.S;
				c !== null && c(o, s), Ko(e, t, s);
			} catch (n) {
				Jo(e, t, n);
			} finally {
				a !== null && o.types !== null && (a.types = o.types), j.T = a;
			}
		} else try {
			a = n(i, r), Ko(e, t, a);
		} catch (n) {
			Jo(e, t, n);
		}
	}
	function Ko(e, t, n) {
		typeof n == "object" && n && typeof n.then == "function" ? n.then(function(n) {
			qo(e, t, n);
		}, function(n) {
			return Jo(e, t, n);
		}) : qo(e, t, n);
	}
	function qo(e, t, n) {
		t.status = "fulfilled", t.value = n, Yo(t), e.state = n, t = e.pending, t !== null && (n = t.next, n === t ? e.pending = null : (n = n.next, t.next = n, Go(e, n)));
	}
	function Jo(e, t, n) {
		var r = e.pending;
		if (e.pending = null, r !== null) {
			r = r.next;
			do
				t.status = "rejected", t.reason = n, Yo(t), t = t.next;
			while (t !== r);
		}
		e.action = null;
	}
	function Yo(e) {
		e = e.listeners;
		for (var t = 0; t < e.length; t++) (0, e[t])();
	}
	function Xo(e, t) {
		return t;
	}
	function Zo(e, t) {
		if (R) {
			var n = Rl.formState;
			if (n !== null) {
				a: {
					var r = G;
					if (R) {
						if (L) {
							b: {
								for (var i = L, a = Li; i.nodeType !== 8;) {
									if (!a) {
										i = null;
										break b;
									}
									if (i = cf(i.nextSibling), i === null) {
										i = null;
										break b;
									}
								}
								a = i.data, i = a === "F!" || a === "F" ? i : null;
							}
							if (i) {
								L = cf(i.nextSibling), r = i.data === "F!";
								break a;
							}
						}
						zi(r);
					}
					r = !1;
				}
				r && (t = n[0]);
			}
		}
		return n = Eo(), n.memoizedState = n.baseState = t, r = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Xo,
			lastRenderedState: t
		}, n.queue = r, n = ks.bind(null, G, r), r.dispatch = n, r = Ho(!1), a = js.bind(null, G, !1, r.queue), r = Eo(), i = {
			state: t,
			dispatch: null,
			action: e,
			pending: null
		}, r.queue = i, n = Wo.bind(null, G, i, a, n), i.dispatch = n, r.memoizedState = e, [
			t,
			n,
			!1
		];
	}
	function Qo(e) {
		return $o(Do(), K, e);
	}
	function $o(e, t, n) {
		if (t = Po(e, t, Xo)[0], e = No(Mo)[0], typeof t == "object" && t && typeof t.then == "function") try {
			var r = ko(t);
		} catch (e) {
			throw e === ya ? W : e;
		}
		else r = t;
		t = Do();
		var i = t.queue, a = i.dispatch;
		return n !== t.memoizedState && (G.flags |= 2048, ns(9, { destroy: void 0 }, es.bind(null, i, n), null)), [
			r,
			a,
			e
		];
	}
	function es(e, t) {
		e.action = t;
	}
	function ts(e) {
		var t = Do(), n = K;
		if (n !== null) return $o(t, n, e);
		Do(), t = t.memoizedState, n = Do();
		var r = n.queue.dispatch;
		return n.memoizedState = e, [
			t,
			r,
			!1
		];
	}
	function ns(e, t, n, r) {
		return e = {
			tag: e,
			create: n,
			deps: r,
			inst: t,
			next: null
		}, t = G.updateQueue, t === null && (t = Oo(), G.updateQueue = t), n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e), e;
	}
	function rs() {
		return Do().memoizedState;
	}
	function is(e, t, n, r) {
		var i = Eo();
		G.flags |= e, i.memoizedState = ns(1 | t, { destroy: void 0 }, n, r === void 0 ? null : r);
	}
	function as(e, t, n, r) {
		var i = Do();
		r = r === void 0 ? null : r;
		var a = i.memoizedState.inst;
		K !== null && r !== null && vo(r, K.memoizedState.deps) ? i.memoizedState = ns(t, a, n, r) : (G.flags |= e, i.memoizedState = ns(1 | t, a, n, r));
	}
	function os(e, t) {
		is(8390656, 8, e, t);
	}
	function ss(e, t) {
		as(2048, 8, e, t);
	}
	function cs(e) {
		G.flags |= 4;
		var t = G.updateQueue;
		if (t === null) t = Oo(), G.updateQueue = t, t.events = [e];
		else {
			var n = t.events;
			n === null ? t.events = [e] : n.push(e);
		}
	}
	function ls(e) {
		var t = Do().memoizedState;
		return cs({
			ref: t,
			nextImpl: e
		}), function() {
			if (q & 2) throw Error(i(440));
			return t.impl.apply(void 0, arguments);
		};
	}
	function us(e, t) {
		return as(4, 2, e, t);
	}
	function ds(e, t) {
		return as(4, 4, e, t);
	}
	function fs(e, t) {
		if (typeof t == "function") {
			e = e();
			var n = t(e);
			return function() {
				typeof n == "function" ? n() : t(null);
			};
		}
		if (t != null) return e = e(), t.current = e, function() {
			t.current = null;
		};
	}
	function ps(e, t, n) {
		n = n == null ? null : n.concat([e]), as(4, 4, fs.bind(null, t, e), n);
	}
	function ms() {}
	function hs(e, t) {
		var n = Do();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return t !== null && vo(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function gs(e, t) {
		var n = Do();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		if (t !== null && vo(t, r[1])) return r[0];
		if (r = e(), fo) {
			Ve(!0);
			try {
				e();
			} finally {
				Ve(!1);
			}
		}
		return n.memoizedState = [r, t], r;
	}
	function _s(e, t, n) {
		return n === void 0 || so & 1073741824 && !(Y & 261930) ? e.memoizedState = t : (e.memoizedState = n, e = mu(), G.lanes |= e, Gl |= e, n);
	}
	function vs(e, t, n, r) {
		return wr(n, t) ? n : qa.current === null ? !(so & 42) || so & 1073741824 && !(Y & 261930) ? (ec = !0, e.memoizedState = n) : (e = mu(), G.lanes |= e, Gl |= e, t) : (e = _s(e, n, r), wr(e, t) || (ec = !0), e);
	}
	function ys(e, t, n, r, i) {
		var a = M.p;
		M.p = a !== 0 && 8 > a ? a : 8;
		var o = j.T, s = {};
		j.T = s, js(e, !1, t, n);
		try {
			var c = i(), l = j.S;
			l !== null && l(s, c), typeof c == "object" && c && typeof c.then == "function" ? As(e, t, ha(c, r), pu(e)) : As(e, t, r, pu(e));
		} catch (n) {
			As(e, t, {
				then: function() {},
				status: "rejected",
				reason: n
			}, pu());
		} finally {
			M.p = a, o !== null && s.types !== null && (o.types = s.types), j.T = o;
		}
	}
	function bs() {}
	function xs(e, t, n, r) {
		if (e.tag !== 5) throw Error(i(476));
		var a = Ss(e).queue;
		ys(e, a, t, ae, n === null ? bs : function() {
			return Cs(e), n(r);
		});
	}
	function Ss(e) {
		var t = e.memoizedState;
		if (t !== null) return t;
		t = {
			memoizedState: ae,
			baseState: ae,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: Mo,
				lastRenderedState: ae
			},
			next: null
		};
		var n = {};
		return t.next = {
			memoizedState: n,
			baseState: n,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: Mo,
				lastRenderedState: n
			},
			next: null
		}, e.memoizedState = t, e = e.alternate, e !== null && (e.memoizedState = t), t;
	}
	function Cs(e) {
		var t = Ss(e);
		t.next === null && (t = e.alternate.memoizedState), As(e, t.next.queue, {}, pu());
	}
	function ws() {
		return z(Qf);
	}
	function Ts() {
		return Do().memoizedState;
	}
	function Es() {
		return Do().memoizedState;
	}
	function Ds(e) {
		for (var t = e.return; t !== null;) {
			switch (t.tag) {
				case 24:
				case 3:
					var n = pu();
					e = Ra(n);
					var r = za(t, e, n);
					r !== null && (hu(r, t, n), Ba(r, t, n)), t = { cache: B() }, e.payload = t;
					return;
			}
			t = t.return;
		}
	}
	function Os(e, t, n) {
		var r = pu();
		n = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, Ms(e) ? Ns(t, n) : (n = ii(e, t, n, r), n !== null && (hu(n, e, r), Ps(n, t, r)));
	}
	function ks(e, t, n) {
		As(e, t, n, pu());
	}
	function As(e, t, n, r) {
		var i = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (Ms(e)) Ns(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, wr(s, o)) return ri(e, t, i, 0), Rl === null && ni(), !1;
			} catch {}
			if (n = ii(e, t, i, r), n !== null) return hu(n, e, r), Ps(n, t, r), !0;
		}
		return !1;
	}
	function js(e, t, n, r) {
		if (r = {
			lane: 2,
			revertLane: dd(),
			gesture: null,
			action: r,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, Ms(e)) {
			if (t) throw Error(i(479));
		} else t = ii(e, n, r, 2), t !== null && hu(t, e, 2);
	}
	function Ms(e) {
		var t = e.alternate;
		return e === G || t !== null && t === G;
	}
	function Ns(e, t) {
		uo = lo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function Ps(e, t, n) {
		if (n & 4194048) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, it(e, n);
		}
	}
	var Fs = {
		readContext: z,
		use: Ao,
		useCallback: _o,
		useContext: _o,
		useEffect: _o,
		useImperativeHandle: _o,
		useLayoutEffect: _o,
		useInsertionEffect: _o,
		useMemo: _o,
		useReducer: _o,
		useRef: _o,
		useState: _o,
		useDebugValue: _o,
		useDeferredValue: _o,
		useTransition: _o,
		useSyncExternalStore: _o,
		useId: _o,
		useHostTransitionStatus: _o,
		useFormState: _o,
		useActionState: _o,
		useOptimistic: _o,
		useMemoCache: _o,
		useCacheRefresh: _o
	};
	Fs.useEffectEvent = _o;
	var Is = {
		readContext: z,
		use: Ao,
		useCallback: function(e, t) {
			return Eo().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: z,
		useEffect: os,
		useImperativeHandle: function(e, t, n) {
			n = n == null ? null : n.concat([e]), is(4194308, 4, fs.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return is(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			is(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = Eo();
			t = t === void 0 ? null : t;
			var r = e();
			if (fo) {
				Ve(!0);
				try {
					e();
				} finally {
					Ve(!1);
				}
			}
			return n.memoizedState = [r, t], r;
		},
		useReducer: function(e, t, n) {
			var r = Eo();
			if (n !== void 0) {
				var i = n(t);
				if (fo) {
					Ve(!0);
					try {
						n(t);
					} finally {
						Ve(!1);
					}
				}
			} else i = t;
			return r.memoizedState = r.baseState = i, e = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: i
			}, r.queue = e, e = e.dispatch = Os.bind(null, G, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = Eo();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: function(e) {
			e = Ho(e);
			var t = e.queue, n = ks.bind(null, G, t);
			return t.dispatch = n, [e.memoizedState, n];
		},
		useDebugValue: ms,
		useDeferredValue: function(e, t) {
			return _s(Eo(), e, t);
		},
		useTransition: function() {
			var e = Ho(!1);
			return e = ys.bind(null, G, e.queue, !0, !1), Eo().memoizedState = e, [!1, e];
		},
		useSyncExternalStore: function(e, t, n) {
			var r = G, a = Eo();
			if (R) {
				if (n === void 0) throw Error(i(407));
				n = n();
			} else {
				if (n = t(), Rl === null) throw Error(i(349));
				Y & 127 || Lo(r, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, os(zo.bind(null, r, o, e), [e]), r.flags |= 2048, ns(9, { destroy: void 0 }, Ro.bind(null, r, o, n, t), null), n;
		},
		useId: function() {
			var e = Eo(), t = Rl.identifierPrefix;
			if (R) {
				var n = ki, r = Oi;
				n = (r & ~(1 << 32 - He(r) - 1)).toString(32) + n, t = "_" + t + "R_" + n, n = po++, 0 < n && (t += "H" + n.toString(32)), t += "_";
			} else n = go++, t = "_" + t + "r_" + n.toString(32) + "_";
			return e.memoizedState = t;
		},
		useHostTransitionStatus: ws,
		useFormState: Zo,
		useActionState: Zo,
		useOptimistic: function(e) {
			var t = Eo();
			t.memoizedState = t.baseState = e;
			var n = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: null,
				lastRenderedState: null
			};
			return t.queue = n, t = js.bind(null, G, !0, n), n.dispatch = t, [e, t];
		},
		useMemoCache: jo,
		useCacheRefresh: function() {
			return Eo().memoizedState = Ds.bind(null, G);
		},
		useEffectEvent: function(e) {
			var t = Eo(), n = { impl: e };
			return t.memoizedState = n, function() {
				if (q & 2) throw Error(i(440));
				return n.impl.apply(void 0, arguments);
			};
		}
	}, Ls = {
		readContext: z,
		use: Ao,
		useCallback: hs,
		useContext: z,
		useEffect: ss,
		useImperativeHandle: ps,
		useInsertionEffect: us,
		useLayoutEffect: ds,
		useMemo: gs,
		useReducer: No,
		useRef: rs,
		useState: function() {
			return No(Mo);
		},
		useDebugValue: ms,
		useDeferredValue: function(e, t) {
			return vs(Do(), K.memoizedState, e, t);
		},
		useTransition: function() {
			var e = No(Mo)[0], t = Do().memoizedState;
			return [typeof e == "boolean" ? e : ko(e), t];
		},
		useSyncExternalStore: Io,
		useId: Ts,
		useHostTransitionStatus: ws,
		useFormState: Qo,
		useActionState: Qo,
		useOptimistic: function(e, t) {
			return Uo(Do(), K, e, t);
		},
		useMemoCache: jo,
		useCacheRefresh: Es
	};
	Ls.useEffectEvent = ls;
	var Rs = {
		readContext: z,
		use: Ao,
		useCallback: hs,
		useContext: z,
		useEffect: ss,
		useImperativeHandle: ps,
		useInsertionEffect: us,
		useLayoutEffect: ds,
		useMemo: gs,
		useReducer: Fo,
		useRef: rs,
		useState: function() {
			return Fo(Mo);
		},
		useDebugValue: ms,
		useDeferredValue: function(e, t) {
			var n = Do();
			return K === null ? _s(n, e, t) : vs(n, K.memoizedState, e, t);
		},
		useTransition: function() {
			var e = Fo(Mo)[0], t = Do().memoizedState;
			return [typeof e == "boolean" ? e : ko(e), t];
		},
		useSyncExternalStore: Io,
		useId: Ts,
		useHostTransitionStatus: ws,
		useFormState: ts,
		useActionState: ts,
		useOptimistic: function(e, t) {
			var n = Do();
			return K === null ? (n.baseState = e, [e, n.queue.dispatch]) : Uo(n, K, e, t);
		},
		useMemoCache: jo,
		useCacheRefresh: Es
	};
	Rs.useEffectEvent = ls;
	function zs(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : h({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var Bs = {
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = pu(), i = Ra(r);
			i.payload = t, n != null && (i.callback = n), t = za(e, i, r), t !== null && (hu(t, e, r), Ba(t, e, r));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = pu(), i = Ra(r);
			i.tag = 1, i.payload = t, n != null && (i.callback = n), t = za(e, i, r), t !== null && (hu(t, e, r), Ba(t, e, r));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = pu(), r = Ra(n);
			r.tag = 2, t != null && (r.callback = t), t = za(e, r, n), t !== null && (hu(t, e, n), Ba(t, e, n));
		}
	};
	function Vs(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Tr(n, r) || !Tr(i, a) : !0;
	}
	function Hs(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && Bs.enqueueReplaceState(t, t.state, null);
	}
	function Us(e, t) {
		var n = t;
		if ("ref" in t) for (var r in n = {}, t) r !== "ref" && (n[r] = t[r]);
		if (e = e.defaultProps) for (var i in n === t && (n = h({}, n)), e) n[i] === void 0 && (n[i] = e[i]);
		return n;
	}
	function Ws(e) {
		Qr(e);
	}
	function Gs(e) {
		console.error(e);
	}
	function Ks(e) {
		Qr(e);
	}
	function qs(e, t) {
		try {
			var n = e.onUncaughtError;
			n(t.value, { componentStack: t.stack });
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function Js(e, t, n) {
		try {
			var r = e.onCaughtError;
			r(n.value, {
				componentStack: n.stack,
				errorBoundary: t.tag === 1 ? t.stateNode : null
			});
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function Ys(e, t, n) {
		return n = Ra(n), n.tag = 3, n.payload = { element: null }, n.callback = function() {
			qs(e, t);
		}, n;
	}
	function Xs(e) {
		return e = Ra(e), e.tag = 3, e;
	}
	function Zs(e, t, n, r) {
		var i = n.type.getDerivedStateFromError;
		if (typeof i == "function") {
			var a = r.value;
			e.payload = function() {
				return i(a);
			}, e.callback = function() {
				Js(t, n, r);
			};
		}
		var o = n.stateNode;
		o !== null && typeof o.componentDidCatch == "function" && (e.callback = function() {
			Js(t, n, r), typeof i != "function" && (ru === null ? ru = /* @__PURE__ */ new Set([this]) : ru.add(this));
			var e = r.stack;
			this.componentDidCatch(r.value, { componentStack: e === null ? "" : e });
		});
	}
	function Qs(e, t, n, r, a) {
		if (n.flags |= 32768, typeof r == "object" && r && typeof r.then == "function") {
			if (t = n.alternate, t !== null && $i(t, n, a, !0), n = Qa.current, n !== null) {
				switch (n.tag) {
					case 31:
					case 13: return $a === null ? Du() : n.alternate === null && Wl === 0 && (Wl = 3), n.flags &= -257, n.flags |= 65536, n.lanes = a, r === ba ? n.flags |= 16384 : (t = n.updateQueue, t === null ? n.updateQueue = /* @__PURE__ */ new Set([r]) : t.add(r), Gu(e, r, a)), !1;
					case 22: return n.flags |= 65536, r === ba ? n.flags |= 16384 : (t = n.updateQueue, t === null ? (t = {
						transitions: null,
						markerInstances: null,
						retryQueue: /* @__PURE__ */ new Set([r])
					}, n.updateQueue = t) : (n = t.retryQueue, n === null ? t.retryQueue = /* @__PURE__ */ new Set([r]) : n.add(r)), Gu(e, r, a)), !1;
				}
				throw Error(i(435, n.tag));
			}
			return Gu(e, r, a), Du(), !1;
		}
		if (R) return t = Qa.current, t === null ? (r !== Ri && (t = Error(i(423), { cause: r }), Gi(bi(t, n))), e = e.current.alternate, e.flags |= 65536, a &= -a, e.lanes |= a, r = bi(r, n), a = Ys(e.stateNode, r, a), Va(e, a), Wl !== 4 && (Wl = 2)) : (!(t.flags & 65536) && (t.flags |= 256), t.flags |= 65536, t.lanes = a, r !== Ri && (e = Error(i(422), { cause: r }), Gi(bi(e, n)))), !1;
		var o = Error(i(520), { cause: r });
		if (o = bi(o, n), Xl === null ? Xl = [o] : Xl.push(o), Wl !== 4 && (Wl = 2), t === null) return !0;
		r = bi(r, n), n = t;
		do {
			switch (n.tag) {
				case 3: return n.flags |= 65536, e = a & -a, n.lanes |= e, e = Ys(n.stateNode, r, e), Va(n, e), !1;
				case 1: if (t = n.type, o = n.stateNode, !(n.flags & 128) && (typeof t.getDerivedStateFromError == "function" || o !== null && typeof o.componentDidCatch == "function" && (ru === null || !ru.has(o)))) return n.flags |= 65536, a &= -a, n.lanes |= a, a = Xs(a), Zs(a, e, n, r), Va(n, a), !1;
			}
			n = n.return;
		} while (n !== null);
		return !1;
	}
	var $s = Error(i(461)), ec = !1;
	function tc(e, t, n, r) {
		t.child = e === null ? Pa(t, null, n, r) : Na(t, e.child, n, r);
	}
	function nc(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		if ("ref" in r) {
			var o = {};
			for (var s in r) s !== "ref" && (o[s] = r[s]);
		} else o = r;
		return ta(t), r = yo(e, t, n, o, a, i), s = Co(), e !== null && !ec ? (wo(e, t, i), Ec(e, t, i)) : (R && s && Mi(t), t.flags |= 1, tc(e, t, r, i), t.child);
	}
	function rc(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !di(a) && a.defaultProps === void 0 && n.compare === null ? (t.tag = 15, t.type = a, ic(e, t, a, r, i)) : (e = mi(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, !Dc(e, i)) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Tr : n, n(o, r) && e.ref === t.ref) return Ec(e, t, i);
		}
		return t.flags |= 1, e = fi(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function ic(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Tr(a, r) && e.ref === t.ref) {
				if (ec = !1, t.pendingProps = r = a, Dc(e, i)) e.flags & 131072 && (ec = !0);
				else return t.lanes = e.lanes, Ec(e, t, i);
			}
		}
		return fc(e, t, n, r, i);
	}
	function ac(e, t, n, r) {
		var i = r.children, a = e === null ? null : e.memoizedState;
		if (e === null && t.stateNode === null && (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), r.mode === "hidden") {
			if (t.flags & 128) {
				if (a = a === null ? n : a.baseLanes | n, e !== null) {
					for (r = t.child = e.child, i = 0; r !== null;) i = i | r.lanes | r.childLanes, r = r.sibling;
					r = i & ~a;
				} else r = 0, t.child = null;
				return sc(e, t, a, n, r);
			}
			if (n & 536870912) t.memoizedState = {
				baseLanes: 0,
				cachePool: null
			}, e !== null && H(t, a === null ? null : a.cachePool), a === null ? Xa() : Ya(t, a), no(t);
			else return r = t.lanes = 536870912, sc(e, t, a === null ? n : a.baseLanes | n, n, r);
		} else a === null ? (e !== null && H(t, null), Xa(), ro(t)) : (H(t, a.cachePool), Ya(t, a), ro(t), t.memoizedState = null);
		return tc(e, t, i, n), t.child;
	}
	function oc(e, t) {
		return e !== null && e.tag === 22 || t.stateNode !== null || (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), t.sibling;
	}
	function sc(e, t, n, r, i) {
		var a = _a();
		return a = a === null ? null : {
			parent: sa._currentValue,
			pool: a
		}, t.memoizedState = {
			baseLanes: n,
			cachePool: a
		}, e !== null && H(t, null), Xa(), no(t), e !== null && $i(e, t, r, !0), t.childLanes = i, null;
	}
	function cc(e, t) {
		return t = xc({
			mode: t.mode,
			children: t.children
		}, e.mode), t.ref = e.ref, e.child = t, t.return = e, t;
	}
	function lc(e, t, n) {
		return Na(t, e.child, null, n), e = cc(t, t.pendingProps), e.flags |= 2, io(t), t.memoizedState = null, e;
	}
	function uc(e, t, n) {
		var r = t.pendingProps, a = !!(t.flags & 128);
		if (t.flags &= -129, e === null) {
			if (R) {
				if (r.mode === "hidden") return e = cc(t, r), t.lanes = 536870912, oc(null, e);
				if (to(t), (e = L) ? (e = rf(e, Li), e = e !== null && e.data === "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Di === null ? null : {
						id: Oi,
						overflow: ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = _i(e), n.return = t, t.child = n, Fi = t, L = null)) : e = null, e === null) throw zi(t);
				return t.lanes = 536870912, null;
			}
			return cc(t, r);
		}
		var o = e.memoizedState;
		if (o !== null) {
			var s = o.dehydrated;
			if (to(t), a) {
				if (t.flags & 256) t.flags &= -257, t = lc(e, t, n);
				else if (t.memoizedState !== null) t.child = e.child, t.flags |= 128, t = null;
				else throw Error(i(558));
			} else if (ec || $i(e, t, n, !1), a = (n & e.childLanes) !== 0, ec || a) {
				if (r = Rl, r !== null && (s = at(r, n), s !== 0 && s !== o.retryLane)) throw o.retryLane = s, ai(e, s), hu(r, e, s), $s;
				Du(), t = lc(e, t, n);
			} else e = o.treeContext, L = cf(s.nextSibling), Fi = t, R = !0, Ii = null, Li = !1, e !== null && Pi(t, e), t = cc(t, r), t.flags |= 4096;
			return t;
		}
		return e = fi(e.child, {
			mode: r.mode,
			children: r.children
		}), e.ref = t.ref, t.child = e, e.return = t, e;
	}
	function dc(e, t) {
		var n = t.ref;
		if (n === null) e !== null && e.ref !== null && (t.flags |= 4194816);
		else {
			if (typeof n != "function" && typeof n != "object") throw Error(i(284));
			(e === null || e.ref !== n) && (t.flags |= 4194816);
		}
	}
	function fc(e, t, n, r, i) {
		return ta(t), n = yo(e, t, n, r, void 0, i), r = Co(), e !== null && !ec ? (wo(e, t, i), Ec(e, t, i)) : (R && r && Mi(t), t.flags |= 1, tc(e, t, n, i), t.child);
	}
	function pc(e, t, n, r, i, a) {
		return ta(t), t.updateQueue = null, n = xo(t, r, n, i), bo(e), r = Co(), e !== null && !ec ? (wo(e, t, a), Ec(e, t, a)) : (R && r && Mi(t), t.flags |= 1, tc(e, t, n, a), t.child);
	}
	function mc(e, t, n, r, i) {
		if (ta(t), t.stateNode === null) {
			var a = ci, o = n.contextType;
			typeof o == "object" && o && (a = z(o)), a = new n(r, a), t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, a.updater = Bs, t.stateNode = a, a._reactInternals = t, a = t.stateNode, a.props = r, a.state = t.memoizedState, a.refs = {}, Ia(t), o = n.contextType, a.context = typeof o == "object" && o ? z(o) : ci, a.state = t.memoizedState, o = n.getDerivedStateFromProps, typeof o == "function" && (zs(t, n, o, r), a.state = t.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof a.getSnapshotBeforeUpdate == "function" || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (o = a.state, typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount(), o !== a.state && Bs.enqueueReplaceState(a, a.state, null), Wa(t, r, a, i), Ua(), a.state = t.memoizedState), typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !0;
		} else if (e === null) {
			a = t.stateNode;
			var s = t.memoizedProps, c = Us(n, s);
			a.props = c;
			var l = a.context, u = n.contextType;
			o = ci, typeof u == "object" && u && (o = z(u));
			var d = n.getDerivedStateFromProps;
			u = typeof d == "function" || typeof a.getSnapshotBeforeUpdate == "function", s = t.pendingProps !== s, u || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (s || l !== o) && Hs(t, a, r, o), Fa = !1;
			var f = t.memoizedState;
			a.state = f, Wa(t, r, a, i), Ua(), l = t.memoizedState, s || f !== l || Fa ? (typeof d == "function" && (zs(t, n, d, r), l = t.memoizedState), (c = Fa || Vs(t, n, c, r, f, l, o)) ? (u || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = l), a.props = r, a.state = l, a.context = o, r = c) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			a = t.stateNode, La(e, t), o = t.memoizedProps, u = Us(n, o), a.props = u, d = t.pendingProps, f = a.context, l = n.contextType, c = ci, typeof l == "object" && l && (c = z(l)), s = n.getDerivedStateFromProps, (l = typeof s == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (o !== d || f !== c) && Hs(t, a, r, c), Fa = !1, f = t.memoizedState, a.state = f, Wa(t, r, a, i), Ua();
			var p = t.memoizedState;
			o !== d || f !== p || Fa || e !== null && e.dependencies !== null && ea(e.dependencies) ? (typeof s == "function" && (zs(t, n, s, r), p = t.memoizedState), (u = Fa || Vs(t, n, u, r, f, p, c) || e !== null && e.dependencies !== null && ea(e.dependencies)) ? (l || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(r, p, c), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(r, p, c)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = p), a.props = r, a.state = p, a.context = c, r = u) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return a = r, dc(e, t), r = !!(t.flags & 128), a || r ? (a = t.stateNode, n = r && typeof n.getDerivedStateFromError != "function" ? null : a.render(), t.flags |= 1, e !== null && r ? (t.child = Na(t, e.child, null, i), t.child = Na(t, null, n, i)) : tc(e, t, n, i), t.memoizedState = a.state, e = t.child) : e = Ec(e, t, i), e;
	}
	function hc(e, t, n, r) {
		return Ui(), t.flags |= 256, tc(e, t, n, r), t.child;
	}
	var gc = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0,
		hydrationErrors: null
	};
	function _c(e) {
		return {
			baseLanes: e,
			cachePool: va()
		};
	}
	function vc(e, t, n) {
		return e = e === null ? 0 : e.childLanes & ~n, t && (e |= Jl), e;
	}
	function yc(e, t, n) {
		var r = t.pendingProps, a = !1, o = !!(t.flags & 128), s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : !!(ao.current & 2)), s && (a = !0, t.flags &= -129), s = !!(t.flags & 32), t.flags &= -33, e === null) {
			if (R) {
				if (a ? eo(t) : ro(t), (e = L) ? (e = rf(e, Li), e = e !== null && e.data !== "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Di === null ? null : {
						id: Oi,
						overflow: ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = _i(e), n.return = t, t.child = n, Fi = t, L = null)) : e = null, e === null) throw zi(t);
				return of(e) ? t.lanes = 32 : t.lanes = 536870912, null;
			}
			var c = r.children;
			return r = r.fallback, a ? (ro(t), a = t.mode, c = xc({
				mode: "hidden",
				children: c
			}, a), r = hi(r, a, n, null), c.return = t, r.return = t, c.sibling = r, t.child = c, r = t.child, r.memoizedState = _c(n), r.childLanes = vc(e, s, n), t.memoizedState = gc, oc(null, r)) : (eo(t), bc(t, c));
		}
		var l = e.memoizedState;
		if (l !== null && (c = l.dehydrated, c !== null)) {
			if (o) t.flags & 256 ? (eo(t), t.flags &= -257, t = Sc(e, t, n)) : t.memoizedState === null ? (ro(t), c = r.fallback, a = t.mode, r = xc({
				mode: "visible",
				children: r.children
			}, a), c = hi(c, a, n, null), c.flags |= 2, r.return = t, c.return = t, r.sibling = c, t.child = r, Na(t, e.child, null, n), r = t.child, r.memoizedState = _c(n), r.childLanes = vc(e, s, n), t.memoizedState = gc, t = oc(null, r)) : (ro(t), t.child = e.child, t.flags |= 128, t = null);
			else if (eo(t), of(c)) {
				if (s = c.nextSibling && c.nextSibling.dataset, s) var u = s.dgst;
				s = u, r = Error(i(419)), r.stack = "", r.digest = s, Gi({
					value: r,
					source: null,
					stack: null
				}), t = Sc(e, t, n);
			} else if (ec || $i(e, t, n, !1), s = (n & e.childLanes) !== 0, ec || s) {
				if (s = Rl, s !== null && (r = at(s, n), r !== 0 && r !== l.retryLane)) throw l.retryLane = r, ai(e, r), hu(s, e, r), $s;
				af(c) || Du(), t = Sc(e, t, n);
			} else af(c) ? (t.flags |= 192, t.child = e.child, t = null) : (e = l.treeContext, L = cf(c.nextSibling), Fi = t, R = !0, Ii = null, Li = !1, e !== null && Pi(t, e), t = bc(t, r.children), t.flags |= 4096);
			return t;
		}
		return a ? (ro(t), c = r.fallback, a = t.mode, l = e.child, u = l.sibling, r = fi(l, {
			mode: "hidden",
			children: r.children
		}), r.subtreeFlags = l.subtreeFlags & 65011712, u === null ? (c = hi(c, a, n, null), c.flags |= 2) : c = fi(u, c), c.return = t, r.return = t, r.sibling = c, t.child = r, oc(null, r), r = t.child, c = e.child.memoizedState, c === null ? c = _c(n) : (a = c.cachePool, a === null ? a = va() : (l = sa._currentValue, a = a.parent === l ? a : {
			parent: l,
			pool: l
		}), c = {
			baseLanes: c.baseLanes | n,
			cachePool: a
		}), r.memoizedState = c, r.childLanes = vc(e, s, n), t.memoizedState = gc, oc(e.child, r)) : (eo(t), n = e.child, e = n.sibling, n = fi(n, {
			mode: "visible",
			children: r.children
		}), n.return = t, n.sibling = null, e !== null && (s = t.deletions, s === null ? (t.deletions = [e], t.flags |= 16) : s.push(e)), t.child = n, t.memoizedState = null, n);
	}
	function bc(e, t) {
		return t = xc({
			mode: "visible",
			children: t
		}, e.mode), t.return = e, e.child = t;
	}
	function xc(e, t) {
		return e = ui(22, e, null, t), e.lanes = 0, e;
	}
	function Sc(e, t, n) {
		return Na(t, e.child, null, n), e = bc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function Cc(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), Zi(e.return, t, n);
	}
	function wc(e, t, n, r, i, a) {
		var o = e.memoizedState;
		o === null ? e.memoizedState = {
			isBackwards: t,
			rendering: null,
			renderingStartTime: 0,
			last: r,
			tail: n,
			tailMode: i,
			treeForkCount: a
		} : (o.isBackwards = t, o.rendering = null, o.renderingStartTime = 0, o.last = r, o.tail = n, o.tailMode = i, o.treeForkCount = a);
	}
	function Tc(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		r = r.children;
		var o = ao.current, s = !!(o & 2);
		if (s ? (o = o & 1 | 2, t.flags |= 128) : o &= 1, N(ao, o), tc(e, t, r, n), r = R ? wi : 0, !s && e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
			if (e.tag === 13) e.memoizedState !== null && Cc(e, n, t);
			else if (e.tag === 19) Cc(e, n, t);
			else if (e.child !== null) {
				e.child.return = e, e = e.child;
				continue;
			}
			if (e === t) break a;
			for (; e.sibling === null;) {
				if (e.return === null || e.return === t) break a;
				e = e.return;
			}
			e.sibling.return = e.return, e = e.sibling;
		}
		switch (i) {
			case "forwards":
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && oo(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), wc(t, !1, i, n, a, r);
				break;
			case "backwards":
			case "unstable_legacy-backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && oo(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				wc(t, !0, n, null, a, r);
				break;
			case "together":
				wc(t, !1, null, null, void 0, r);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function Ec(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), Gl |= t.lanes, (n & t.childLanes) === 0) {
			if (e !== null) {
				if ($i(e, t, n, !1), (n & t.childLanes) === 0) return null;
			} else return null;
		}
		if (e !== null && t.child !== e.child) throw Error(i(153));
		if (t.child !== null) {
			for (e = t.child, n = fi(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = fi(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function Dc(e, t) {
		return (e.lanes & t) !== 0 || (e = e.dependencies, !!(e !== null && ea(e)));
	}
	function Oc(e, t, n) {
		switch (t.tag) {
			case 3:
				me(t, t.stateNode.containerInfo), Yi(t, sa, e.memoizedState.cache), Ui();
				break;
			case 27:
			case 5:
				ge(t);
				break;
			case 4:
				me(t, t.stateNode.containerInfo);
				break;
			case 10:
				Yi(t, t.type, t.memoizedProps.value);
				break;
			case 31:
				if (t.memoizedState !== null) return t.flags |= 128, to(t), null;
				break;
			case 13:
				var r = t.memoizedState;
				if (r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (eo(t), e = Ec(e, t, n), e === null ? null : e.sibling) : yc(e, t, n) : (eo(t), t.flags |= 128, null);
				eo(t);
				break;
			case 19:
				var i = !!(e.flags & 128);
				if (r = (n & t.childLanes) !== 0, r || ($i(e, t, n, !1), r = (n & t.childLanes) !== 0), i) {
					if (r) return Tc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), N(ao, ao.current), r) break;
				return null;
			case 22: return t.lanes = 0, ac(e, t, n, t.pendingProps);
			case 24: Yi(t, sa, e.memoizedState.cache);
		}
		return Ec(e, t, n);
	}
	function kc(e, t, n) {
		if (e !== null) {
			if (e.memoizedProps !== t.pendingProps) ec = !0;
			else {
				if (!Dc(e, n) && !(t.flags & 128)) return ec = !1, Oc(e, t, n);
				ec = !!(e.flags & 131072);
			}
		} else ec = !1, R && t.flags & 1048576 && ji(t, wi, t.index);
		switch (t.lanes = 0, t.tag) {
			case 16:
				a: {
					var r = t.pendingProps;
					if (e = Ca(t.elementType), t.type = e, typeof e == "function") di(e) ? (r = Us(e, r), t.tag = 1, t = mc(null, t, e, r, n)) : (t.tag = 0, t = fc(null, t, e, r, n));
					else {
						if (e != null) {
							var a = e.$$typeof;
							if (a === w) {
								t.tag = 11, t = nc(null, t, e, r, n);
								break a;
							}
							if (a === D) {
								t.tag = 14, t = rc(null, t, e, r, n);
								break a;
							}
						}
						throw t = ie(e) || e, Error(i(306, t, ""));
					}
				}
				return t;
			case 0: return fc(e, t, t.type, t.pendingProps, n);
			case 1: return r = t.type, a = Us(r, t.pendingProps), mc(e, t, r, a, n);
			case 3:
				a: {
					if (me(t, t.stateNode.containerInfo), e === null) throw Error(i(387));
					r = t.pendingProps;
					var o = t.memoizedState;
					a = o.element, La(e, t), Wa(t, r, null, n);
					var s = t.memoizedState;
					if (r = s.cache, Yi(t, sa, r), r !== o.cache && Qi(t, [sa], n, !0), Ua(), r = s.element, o.isDehydrated) {
						if (o = {
							element: r,
							isDehydrated: !1,
							cache: s.cache
						}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
							t = hc(e, t, r, n);
							break a;
						}
						if (r !== a) {
							a = bi(Error(i(424)), t), Gi(a), t = hc(e, t, r, n);
							break a;
						}
						switch (e = t.stateNode.containerInfo, e.nodeType) {
							case 9:
								e = e.body;
								break;
							default: e = e.nodeName === "HTML" ? e.ownerDocument.body : e;
						}
						for (L = cf(e.firstChild), Fi = t, R = !0, Ii = null, Li = !0, n = Pa(t, null, r, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					} else {
						if (Ui(), r === a) {
							t = Ec(e, t, n);
							break a;
						}
						tc(e, t, r, n);
					}
					t = t.child;
				}
				return t;
			case 26: return dc(e, t), e === null ? (n = kf(t.type, null, t.pendingProps, null)) ? t.memoizedState = n : R || (n = t.type, e = t.pendingProps, r = Bd(fe.current).createElement(n), r[dt] = t, r[ft] = e, Pd(r, n, e), wt(r), t.stateNode = r) : t.memoizedState = kf(t.type, e.memoizedProps, t.pendingProps, e.memoizedState), null;
			case 27: return ge(t), e === null && R && (r = t.stateNode = ff(t.type, t.pendingProps, fe.current), Fi = t, Li = !0, a = L, Zd(t.type) ? (lf = a, L = cf(r.firstChild)) : L = a), tc(e, t, t.pendingProps.children, n), dc(e, t), e === null && (t.flags |= 4194304), t.child;
			case 5: return e === null && R && ((a = r = L) && (r = tf(r, t.type, t.pendingProps, Li), r === null ? a = !1 : (t.stateNode = r, Fi = t, L = cf(r.firstChild), Li = !1, a = !0)), a || zi(t)), ge(t), a = t.type, o = t.pendingProps, s = e === null ? null : e.memoizedProps, r = o.children, Ud(a, o) ? r = null : s !== null && Ud(a, s) && (t.flags |= 32), t.memoizedState !== null && (a = yo(e, t, So, null, null, n), Qf._currentValue = a), dc(e, t), tc(e, t, r, n), t.child;
			case 6: return e === null && R && ((e = n = L) && (n = nf(n, t.pendingProps, Li), n === null ? e = !1 : (t.stateNode = n, Fi = t, L = null, e = !0)), e || zi(t)), null;
			case 13: return yc(e, t, n);
			case 4: return me(t, t.stateNode.containerInfo), r = t.pendingProps, e === null ? t.child = Na(t, null, r, n) : tc(e, t, r, n), t.child;
			case 11: return nc(e, t, t.type, t.pendingProps, n);
			case 7: return tc(e, t, t.pendingProps, n), t.child;
			case 8: return tc(e, t, t.pendingProps.children, n), t.child;
			case 12: return tc(e, t, t.pendingProps.children, n), t.child;
			case 10: return r = t.pendingProps, Yi(t, t.type, r.value), tc(e, t, r.children, n), t.child;
			case 9: return a = t.type._context, r = t.pendingProps.children, ta(t), a = z(a), r = r(a), t.flags |= 1, tc(e, t, r, n), t.child;
			case 14: return rc(e, t, t.type, t.pendingProps, n);
			case 15: return ic(e, t, t.type, t.pendingProps, n);
			case 19: return Tc(e, t, n);
			case 31: return uc(e, t, n);
			case 22: return ac(e, t, n, t.pendingProps);
			case 24: return ta(t), r = z(sa), e === null ? (a = _a(), a === null && (a = Rl, o = B(), a.pooledCache = o, o.refCount++, o !== null && (a.pooledCacheLanes |= n), a = o), t.memoizedState = {
				parent: r,
				cache: a
			}, Ia(t), Yi(t, sa, a)) : ((e.lanes & n) !== 0 && (La(e, t), Wa(t, null, null, n), Ua()), a = e.memoizedState, o = t.memoizedState, a.parent === r ? (r = o.cache, Yi(t, sa, r), r !== a.cache && Qi(t, [sa], n, !0)) : (a = {
				parent: r,
				cache: r
			}, t.memoizedState = a, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = a), Yi(t, sa, r))), tc(e, t, t.pendingProps.children, n), t.child;
			case 29: throw t.pendingProps;
		}
		throw Error(i(156, t.tag));
	}
	function Ac(e) {
		e.flags |= 4;
	}
	function jc(e, t, n, r, i) {
		if ((t = !!(e.mode & 32)) && (t = !1), t) {
			if (e.flags |= 16777216, (i & 335544128) === i) {
				if (e.stateNode.complete) e.flags |= 8192;
				else if (wu()) e.flags |= 8192;
				else throw wa = ba, U;
			}
		} else e.flags &= -16777217;
	}
	function Mc(e, t) {
		if (t.type !== "stylesheet" || t.state.loading & 4) e.flags &= -16777217;
		else if (e.flags |= 16777216, !Wf(t)) {
			if (wu()) e.flags |= 8192;
			else throw wa = ba, U;
		}
	}
	function Nc(e, t) {
		t !== null && (e.flags |= 4), e.flags & 16384 && (t = e.tag === 22 ? 536870912 : $e(), e.lanes |= t, Yl |= t);
	}
	function Pc(e, t) {
		if (!R) switch (e.tailMode) {
			case "hidden":
				t = e.tail;
				for (var n = null; t !== null;) t.alternate !== null && (n = t), t = t.sibling;
				n === null ? e.tail = null : n.sibling = null;
				break;
			case "collapsed":
				n = e.tail;
				for (var r = null; n !== null;) n.alternate !== null && (r = n), n = n.sibling;
				r === null ? t || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
		}
	}
	function Fc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 65011712, r |= i.flags & 65011712, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function Ic(e, t, n) {
		var r = t.pendingProps;
		switch (Ni(t), t.tag) {
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return Fc(t), null;
			case 1: return Fc(t), null;
			case 3: return n = t.stateNode, r = null, e !== null && (r = e.memoizedState.cache), t.memoizedState.cache !== r && (t.flags |= 2048), Xi(sa), he(), n.pendingContext && (n.context = n.pendingContext, n.pendingContext = null), (e === null || e.child === null) && (Hi(t) ? Ac(t) : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Wi())), Fc(t), null;
			case 26:
				var a = t.type, o = t.memoizedState;
				return e === null ? (Ac(t), o === null ? (Fc(t), jc(t, a, null, r, n)) : (Fc(t), Mc(t, o))) : o ? o === e.memoizedState ? (Fc(t), t.flags &= -16777217) : (Ac(t), Fc(t), Mc(t, o)) : (e = e.memoizedProps, e !== r && Ac(t), Fc(t), jc(t, a, e, r, n)), null;
			case 27:
				if (_e(t), n = fe.current, a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && Ac(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return Fc(t), null;
					}
					e = ue.current, Hi(t) ? Bi(t, e) : (e = ff(a, r, n), t.stateNode = e, Ac(t));
				}
				return Fc(t), null;
			case 5:
				if (_e(t), a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && Ac(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return Fc(t), null;
					}
					if (o = ue.current, Hi(t)) Bi(t, o);
					else {
						var s = Bd(fe.current);
						switch (o) {
							case 1:
								o = s.createElementNS("http://www.w3.org/2000/svg", a);
								break;
							case 2:
								o = s.createElementNS("http://www.w3.org/1998/Math/MathML", a);
								break;
							default: switch (a) {
								case "svg":
									o = s.createElementNS("http://www.w3.org/2000/svg", a);
									break;
								case "math":
									o = s.createElementNS("http://www.w3.org/1998/Math/MathML", a);
									break;
								case "script":
									o = s.createElement("div"), o.innerHTML = "<script><\/script>", o = o.removeChild(o.firstChild);
									break;
								case "select":
									o = typeof r.is == "string" ? s.createElement("select", { is: r.is }) : s.createElement("select"), r.multiple ? o.multiple = !0 : r.size && (o.size = r.size);
									break;
								default: o = typeof r.is == "string" ? s.createElement(a, { is: r.is }) : s.createElement(a);
							}
						}
						o[dt] = t, o[ft] = r;
						a: for (s = t.child; s !== null;) {
							if (s.tag === 5 || s.tag === 6) o.appendChild(s.stateNode);
							else if (s.tag !== 4 && s.tag !== 27 && s.child !== null) {
								s.child.return = s, s = s.child;
								continue;
							}
							if (s === t) break a;
							for (; s.sibling === null;) {
								if (s.return === null || s.return === t) break a;
								s = s.return;
							}
							s.sibling.return = s.return, s = s.sibling;
						}
						t.stateNode = o;
						a: switch (Pd(o, a, r), a) {
							case "button":
							case "input":
							case "select":
							case "textarea":
								r = !!r.autoFocus;
								break a;
							case "img":
								r = !0;
								break a;
							default: r = !1;
						}
						r && Ac(t);
					}
				}
				return Fc(t), jc(t, t.type, e === null ? null : e.memoizedProps, t.pendingProps, n), null;
			case 6:
				if (e && t.stateNode != null) e.memoizedProps !== r && Ac(t);
				else {
					if (typeof r != "string" && t.stateNode === null) throw Error(i(166));
					if (e = fe.current, Hi(t)) {
						if (e = t.stateNode, n = t.memoizedProps, r = null, a = Fi, a !== null) switch (a.tag) {
							case 27:
							case 5: r = a.memoizedProps;
						}
						e[dt] = t, e = !!(e.nodeValue === n || r !== null && !0 === r.suppressHydrationWarning || Md(e.nodeValue, n)), e || zi(t, !0);
					} else e = Bd(e).createTextNode(r), e[dt] = t, t.stateNode = e;
				}
				return Fc(t), null;
			case 31:
				if (n = t.memoizedState, e === null || e.memoizedState !== null) {
					if (r = Hi(t), n !== null) {
						if (e === null) {
							if (!r) throw Error(i(318));
							if (e = t.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(557));
							e[dt] = t;
						} else Ui(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						Fc(t), e = !1;
					} else n = Wi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = n), e = !0;
					if (!e) return t.flags & 256 ? (io(t), t) : (io(t), null);
					if (t.flags & 128) throw Error(i(558));
				}
				return Fc(t), null;
			case 13:
				if (r = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (a = Hi(t), r !== null && r.dehydrated !== null) {
						if (e === null) {
							if (!a) throw Error(i(318));
							if (a = t.memoizedState, a = a === null ? null : a.dehydrated, !a) throw Error(i(317));
							a[dt] = t;
						} else Ui(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						Fc(t), a = !1;
					} else a = Wi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = a), a = !0;
					if (!a) return t.flags & 256 ? (io(t), t) : (io(t), null);
				}
				return io(t), t.flags & 128 ? (t.lanes = n, t) : (n = r !== null, e = e !== null && e.memoizedState !== null, n && (r = t.child, a = null, r.alternate !== null && r.alternate.memoizedState !== null && r.alternate.memoizedState.cachePool !== null && (a = r.alternate.memoizedState.cachePool.pool), o = null, r.memoizedState !== null && r.memoizedState.cachePool !== null && (o = r.memoizedState.cachePool.pool), o !== a && (r.flags |= 2048)), n !== e && n && (t.child.flags |= 8192), Nc(t, t.updateQueue), Fc(t), null);
			case 4: return he(), e === null && Sd(t.stateNode.containerInfo), Fc(t), null;
			case 10: return Xi(t.type), Fc(t), null;
			case 19:
				if (le(ao), r = t.memoizedState, r === null) return Fc(t), null;
				if (a = !!(t.flags & 128), o = r.rendering, o === null) {
					if (a) Pc(r, !1);
					else {
						if (Wl !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
							if (o = oo(e), o !== null) {
								for (t.flags |= 128, Pc(r, !1), e = o.updateQueue, t.updateQueue = e, Nc(t, e), t.subtreeFlags = 0, e = n, n = t.child; n !== null;) pi(n, e), n = n.sibling;
								return N(ao, ao.current & 1 | 2), R && Ai(t, r.treeForkCount), t.child;
							}
							e = e.sibling;
						}
						r.tail !== null && Ae() > tu && (t.flags |= 128, a = !0, Pc(r, !1), t.lanes = 4194304);
					}
				} else {
					if (!a) {
						if (e = oo(o), e !== null) {
							if (t.flags |= 128, a = !0, e = e.updateQueue, t.updateQueue = e, Nc(t, e), Pc(r, !0), r.tail === null && r.tailMode === "hidden" && !o.alternate && !R) return Fc(t), null;
						} else 2 * Ae() - r.renderingStartTime > tu && n !== 536870912 && (t.flags |= 128, a = !0, Pc(r, !1), t.lanes = 4194304);
					}
					r.isBackwards ? (o.sibling = t.child, t.child = o) : (e = r.last, e === null ? t.child = o : e.sibling = o, r.last = o);
				}
				return r.tail === null ? (Fc(t), null) : (e = r.tail, r.rendering = e, r.tail = e.sibling, r.renderingStartTime = Ae(), e.sibling = null, n = ao.current, N(ao, a ? n & 1 | 2 : n & 1), R && Ai(t, r.treeForkCount), e);
			case 22:
			case 23: return io(t), Za(), r = t.memoizedState !== null, e === null ? r && (t.flags |= 8192) : e.memoizedState !== null !== r && (t.flags |= 8192), r ? n & 536870912 && !(t.flags & 128) && (Fc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : Fc(t), n = t.updateQueue, n !== null && Nc(t, n.retryQueue), n = null, e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), r = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (r = t.memoizedState.cachePool.pool), r !== n && (t.flags |= 2048), e !== null && le(ga), null;
			case 24: return n = null, e !== null && (n = e.memoizedState.cache), t.memoizedState.cache !== n && (t.flags |= 2048), Xi(sa), Fc(t), null;
			case 25: return null;
			case 30: return null;
		}
		throw Error(i(156, t.tag));
	}
	function Lc(e, t) {
		switch (Ni(t), t.tag) {
			case 1: return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return Xi(sa), he(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 26:
			case 27:
			case 5: return _e(t), null;
			case 31:
				if (t.memoizedState !== null) {
					if (io(t), t.alternate === null) throw Error(i(340));
					Ui();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 13:
				if (io(t), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(i(340));
					Ui();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return le(ao), null;
			case 4: return he(), null;
			case 10: return Xi(t.type), null;
			case 22:
			case 23: return io(t), Za(), e !== null && le(ga), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 24: return Xi(sa), null;
			case 25: return null;
			default: return null;
		}
	}
	function Rc(e, t) {
		switch (Ni(t), t.tag) {
			case 3:
				Xi(sa), he();
				break;
			case 26:
			case 27:
			case 5:
				_e(t);
				break;
			case 4:
				he();
				break;
			case 31:
				t.memoizedState !== null && io(t);
				break;
			case 13:
				io(t);
				break;
			case 19:
				le(ao);
				break;
			case 10:
				Xi(t.type);
				break;
			case 22:
			case 23:
				io(t), Za(), e !== null && le(ga);
				break;
			case 24: Xi(sa);
		}
	}
	function zc(e, t) {
		try {
			var n = t.updateQueue, r = n === null ? null : n.lastEffect;
			if (r !== null) {
				var i = r.next;
				n = i;
				do {
					if ((n.tag & e) === e) {
						r = void 0;
						var a = n.create, o = n.inst;
						r = a(), o.destroy = r;
					}
					n = n.next;
				} while (n !== i);
			}
		} catch (e) {
			Z(t, t.return, e);
		}
	}
	function Bc(e, t, n) {
		try {
			var r = t.updateQueue, i = r === null ? null : r.lastEffect;
			if (i !== null) {
				var a = i.next;
				r = a;
				do {
					if ((r.tag & e) === e) {
						var o = r.inst, s = o.destroy;
						if (s !== void 0) {
							o.destroy = void 0, i = t;
							var c = n, l = s;
							try {
								l();
							} catch (e) {
								Z(i, c, e);
							}
						}
					}
					r = r.next;
				} while (r !== a);
			}
		} catch (e) {
			Z(t, t.return, e);
		}
	}
	function Vc(e) {
		var t = e.updateQueue;
		if (t !== null) {
			var n = e.stateNode;
			try {
				Ka(t, n);
			} catch (t) {
				Z(e, e.return, t);
			}
		}
	}
	function Hc(e, t, n) {
		n.props = Us(e.type, e.memoizedProps), n.state = e.memoizedState;
		try {
			n.componentWillUnmount();
		} catch (n) {
			Z(e, t, n);
		}
	}
	function Uc(e, t) {
		try {
			var n = e.ref;
			if (n !== null) {
				switch (e.tag) {
					case 26:
					case 27:
					case 5:
						var r = e.stateNode;
						break;
					case 30:
						r = e.stateNode;
						break;
					default: r = e.stateNode;
				}
				typeof n == "function" ? e.refCleanup = n(r) : n.current = r;
			}
		} catch (n) {
			Z(e, t, n);
		}
	}
	function Wc(e, t) {
		var n = e.ref, r = e.refCleanup;
		if (n !== null) {
			if (typeof r == "function") try {
				r();
			} catch (n) {
				Z(e, t, n);
			} finally {
				e.refCleanup = null, e = e.alternate, e != null && (e.refCleanup = null);
			}
			else if (typeof n == "function") try {
				n(null);
			} catch (n) {
				Z(e, t, n);
			}
			else n.current = null;
		}
	}
	function Gc(e) {
		var t = e.type, n = e.memoizedProps, r = e.stateNode;
		try {
			a: switch (t) {
				case "button":
				case "input":
				case "select":
				case "textarea":
					n.autoFocus && r.focus();
					break a;
				case "img": n.src ? r.src = n.src : n.srcSet && (r.srcset = n.srcSet);
			}
		} catch (t) {
			Z(e, e.return, t);
		}
	}
	function Kc(e, t, n) {
		try {
			var r = e.stateNode;
			Fd(r, e.type, n, t), r[ft] = t;
		} catch (t) {
			Z(e, e.return, t);
		}
	}
	function qc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 26 || e.tag === 27 && Zd(e.type) || e.tag === 4;
	}
	function Jc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || qc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.tag === 27 && Zd(e.type) || e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Yc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? (n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n).insertBefore(e, t) : (t = n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n, t.appendChild(e), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = an));
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode, t = null), e = e.child, e !== null)) for (Yc(e, t, n), e = e.sibling; e !== null;) Yc(e, t, n), e = e.sibling;
	}
	function Xc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode), e = e.child, e !== null)) for (Xc(e, t, n), e = e.sibling; e !== null;) Xc(e, t, n), e = e.sibling;
	}
	function Zc(e) {
		var t = e.stateNode, n = e.memoizedProps;
		try {
			for (var r = e.type, i = t.attributes; i.length;) t.removeAttributeNode(i[0]);
			Pd(t, r, n), t[dt] = e, t[ft] = n;
		} catch (t) {
			Z(e, e.return, t);
		}
	}
	var Qc = !1, $c = !1, el = !1, tl = typeof WeakSet == "function" ? WeakSet : Set, nl = null;
	function rl(e, t) {
		if (e = e.containerInfo, Rd = sp, e = kr(e), Ar(e)) {
			if ("selectionStart" in e) var n = {
				start: e.selectionStart,
				end: e.selectionEnd
			};
			else a: {
				n = (n = e.ownerDocument) && n.defaultView || window;
				var r = n.getSelection && n.getSelection();
				if (r && r.rangeCount !== 0) {
					n = r.anchorNode;
					var a = r.anchorOffset, o = r.focusNode;
					r = r.focusOffset;
					try {
						n.nodeType, o.nodeType;
					} catch {
						n = null;
						break a;
					}
					var s = 0, c = -1, l = -1, u = 0, d = 0, f = e, p = null;
					b: for (;;) {
						for (var m; f !== n || a !== 0 && f.nodeType !== 3 || (c = s + a), f !== o || r !== 0 && f.nodeType !== 3 || (l = s + r), f.nodeType === 3 && (s += f.nodeValue.length), (m = f.firstChild) !== null;) p = f, f = m;
						for (;;) {
							if (f === e) break b;
							if (p === n && ++u === a && (c = s), p === o && ++d === r && (l = s), (m = f.nextSibling) !== null) break;
							f = p, p = f.parentNode;
						}
						f = m;
					}
					n = c === -1 || l === -1 ? null : {
						start: c,
						end: l
					};
				} else n = null;
			}
			n = n || {
				start: 0,
				end: 0
			};
		} else n = null;
		for (zd = {
			focusedElem: e,
			selectionRange: n
		}, sp = !1, nl = t; nl !== null;) if (t = nl, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, nl = e;
		else for (; nl !== null;) {
			switch (t = nl, o = t.alternate, e = t.flags, t.tag) {
				case 0:
					if (e & 4 && (e = t.updateQueue, e = e === null ? null : e.events, e !== null)) for (n = 0; n < e.length; n++) a = e[n], a.ref.impl = a.nextImpl;
					break;
				case 11:
				case 15: break;
				case 1:
					if (e & 1024 && o !== null) {
						e = void 0, n = t, a = o.memoizedProps, o = o.memoizedState, r = n.stateNode;
						try {
							var h = Us(n.type, a);
							e = r.getSnapshotBeforeUpdate(h, o), r.__reactInternalSnapshotBeforeUpdate = e;
						} catch (e) {
							Z(n, n.return, e);
						}
					}
					break;
				case 3:
					if (e & 1024) {
						if (e = t.stateNode.containerInfo, n = e.nodeType, n === 9) ef(e);
						else if (n === 1) switch (e.nodeName) {
							case "HEAD":
							case "HTML":
							case "BODY":
								ef(e);
								break;
							default: e.textContent = "";
						}
					}
					break;
				case 5:
				case 26:
				case 27:
				case 6:
				case 4:
				case 17: break;
				default: if (e & 1024) throw Error(i(163));
			}
			if (e = t.sibling, e !== null) {
				e.return = t.return, nl = e;
				break;
			}
			nl = t.return;
		}
	}
	function il(e, t, n) {
		var r = n.flags;
		switch (n.tag) {
			case 0:
			case 11:
			case 15:
				yl(e, n), r & 4 && zc(5, n);
				break;
			case 1:
				if (yl(e, n), r & 4) {
					if (e = n.stateNode, t === null) try {
						e.componentDidMount();
					} catch (e) {
						Z(n, n.return, e);
					}
					else {
						var i = Us(n.type, t.memoizedProps);
						t = t.memoizedState;
						try {
							e.componentDidUpdate(i, t, e.__reactInternalSnapshotBeforeUpdate);
						} catch (e) {
							Z(n, n.return, e);
						}
					}
				}
				r & 64 && Vc(n), r & 512 && Uc(n, n.return);
				break;
			case 3:
				if (yl(e, n), r & 64 && (e = n.updateQueue, e !== null)) {
					if (t = null, n.child !== null) switch (n.child.tag) {
						case 27:
						case 5:
							t = n.child.stateNode;
							break;
						case 1: t = n.child.stateNode;
					}
					try {
						Ka(e, t);
					} catch (e) {
						Z(n, n.return, e);
					}
				}
				break;
			case 27: t === null && r & 4 && Zc(n);
			case 26:
			case 5:
				yl(e, n), t === null && r & 4 && Gc(n), r & 512 && Uc(n, n.return);
				break;
			case 12:
				yl(e, n);
				break;
			case 31:
				yl(e, n), r & 4 && ul(e, n);
				break;
			case 13:
				yl(e, n), r & 4 && dl(e, n), r & 64 && (e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null && (n = Ju.bind(null, n), sf(e, n))));
				break;
			case 22:
				if (r = n.memoizedState !== null || Qc, !r) {
					t = t !== null && t.memoizedState !== null || $c, i = Qc;
					var a = $c;
					Qc = r, ($c = t) && !a ? xl(e, n, !!(n.subtreeFlags & 8772)) : yl(e, n), Qc = i, $c = a;
				}
				break;
			case 30: break;
			default: yl(e, n);
		}
	}
	function al(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, al(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && yt(t)), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	var ol = null, sl = !1;
	function cl(e, t, n) {
		for (n = n.child; n !== null;) ll(e, t, n), n = n.sibling;
	}
	function ll(e, t, n) {
		if (Be && typeof Be.onCommitFiberUnmount == "function") try {
			Be.onCommitFiberUnmount(ze, n);
		} catch {}
		switch (n.tag) {
			case 26:
				$c || Wc(n, t), cl(e, t, n), n.memoizedState ? n.memoizedState.count-- : n.stateNode && (n = n.stateNode, n.parentNode.removeChild(n));
				break;
			case 27:
				$c || Wc(n, t);
				var r = ol, i = sl;
				Zd(n.type) && (ol = n.stateNode, sl = !1), cl(e, t, n), pf(n.stateNode), ol = r, sl = i;
				break;
			case 5: $c || Wc(n, t);
			case 6:
				if (r = ol, i = sl, ol = null, cl(e, t, n), ol = r, sl = i, ol !== null) {
					if (sl) try {
						(ol.nodeType === 9 ? ol.body : ol.nodeName === "HTML" ? ol.ownerDocument.body : ol).removeChild(n.stateNode);
					} catch (e) {
						Z(n, t, e);
					}
					else try {
						ol.removeChild(n.stateNode);
					} catch (e) {
						Z(n, t, e);
					}
				}
				break;
			case 18:
				ol !== null && (sl ? (e = ol, Qd(e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, n.stateNode), Np(e)) : Qd(ol, n.stateNode));
				break;
			case 4:
				r = ol, i = sl, ol = n.stateNode.containerInfo, sl = !0, cl(e, t, n), ol = r, sl = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				Bc(2, n, t), $c || Bc(4, n, t), cl(e, t, n);
				break;
			case 1:
				$c || (Wc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function" && Hc(n, t, r)), cl(e, t, n);
				break;
			case 21:
				cl(e, t, n);
				break;
			case 22:
				$c = (r = $c) || n.memoizedState !== null, cl(e, t, n), $c = r;
				break;
			default: cl(e, t, n);
		}
	}
	function ul(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null))) {
			e = e.dehydrated;
			try {
				Np(e);
			} catch (e) {
				Z(t, t.return, e);
			}
		}
	}
	function dl(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null && (e = e.dehydrated, e !== null)))) try {
			Np(e);
		} catch (e) {
			Z(t, t.return, e);
		}
	}
	function fl(e) {
		switch (e.tag) {
			case 31:
			case 13:
			case 19:
				var t = e.stateNode;
				return t === null && (t = e.stateNode = new tl()), t;
			case 22: return e = e.stateNode, t = e._retryCache, t === null && (t = e._retryCache = new tl()), t;
			default: throw Error(i(435, e.tag));
		}
	}
	function pl(e, t) {
		var n = fl(e);
		t.forEach(function(t) {
			if (!n.has(t)) {
				n.add(t);
				var r = Yu.bind(null, e, t);
				t.then(r, r);
			}
		});
	}
	function ml(e, t) {
		var n = t.deletions;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var a = n[r], o = e, s = t, c = s;
			a: for (; c !== null;) {
				switch (c.tag) {
					case 27:
						if (Zd(c.type)) {
							ol = c.stateNode, sl = !1;
							break a;
						}
						break;
					case 5:
						ol = c.stateNode, sl = !1;
						break a;
					case 3:
					case 4:
						ol = c.stateNode.containerInfo, sl = !0;
						break a;
				}
				c = c.return;
			}
			if (ol === null) throw Error(i(160));
			ll(o, s, a), ol = null, sl = !1, o = a.alternate, o !== null && (o.return = null), a.return = null;
		}
		if (t.subtreeFlags & 13886) for (t = t.child; t !== null;) gl(t, e), t = t.sibling;
	}
	var hl = null;
	function gl(e, t) {
		var n = e.alternate, r = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				ml(t, e), _l(e), r & 4 && (Bc(3, e, e.return), zc(3, e), Bc(5, e, e.return));
				break;
			case 1:
				ml(t, e), _l(e), r & 512 && ($c || n === null || Wc(n, n.return)), r & 64 && Qc && (e = e.updateQueue, e !== null && (r = e.callbacks, r !== null && (n = e.shared.hiddenCallbacks, e.shared.hiddenCallbacks = n === null ? r : n.concat(r))));
				break;
			case 26:
				var a = hl;
				if (ml(t, e), _l(e), r & 512 && ($c || n === null || Wc(n, n.return)), r & 4) {
					var o = n === null ? null : n.memoizedState;
					if (r = e.memoizedState, n === null) {
						if (r === null) {
							if (e.stateNode === null) {
								a: {
									r = e.type, n = e.memoizedProps, a = a.ownerDocument || a;
									b: switch (r) {
										case "title":
											o = a.getElementsByTagName("title")[0], (!o || o[vt] || o[dt] || o.namespaceURI === "http://www.w3.org/2000/svg" || o.hasAttribute("itemprop")) && (o = a.createElement(r), a.head.insertBefore(o, a.querySelector("head > title"))), Pd(o, r, n), o[dt] = e, wt(o), r = o;
											break a;
										case "link":
											var s = Vf("link", "href", a).get(r + (n.href || ""));
											if (s) {
												for (var c = 0; c < s.length; c++) if (o = s[c], o.getAttribute("href") === (n.href == null || n.href === "" ? null : n.href) && o.getAttribute("rel") === (n.rel == null ? null : n.rel) && o.getAttribute("title") === (n.title == null ? null : n.title) && o.getAttribute("crossorigin") === (n.crossOrigin == null ? null : n.crossOrigin)) {
													s.splice(c, 1);
													break b;
												}
											}
											o = a.createElement(r), Pd(o, r, n), a.head.appendChild(o);
											break;
										case "meta":
											if (s = Vf("meta", "content", a).get(r + (n.content || ""))) {
												for (c = 0; c < s.length; c++) if (o = s[c], o.getAttribute("content") === (n.content == null ? null : "" + n.content) && o.getAttribute("name") === (n.name == null ? null : n.name) && o.getAttribute("property") === (n.property == null ? null : n.property) && o.getAttribute("http-equiv") === (n.httpEquiv == null ? null : n.httpEquiv) && o.getAttribute("charset") === (n.charSet == null ? null : n.charSet)) {
													s.splice(c, 1);
													break b;
												}
											}
											o = a.createElement(r), Pd(o, r, n), a.head.appendChild(o);
											break;
										default: throw Error(i(468, r));
									}
									o[dt] = e, wt(o), r = o;
								}
								e.stateNode = r;
							} else Hf(a, e.type, e.stateNode);
						} else e.stateNode = If(a, r, e.memoizedProps);
					} else o === r ? r === null && e.stateNode !== null && Kc(e, e.memoizedProps, n.memoizedProps) : (o === null ? n.stateNode !== null && (n = n.stateNode, n.parentNode.removeChild(n)) : o.count--, r === null ? Hf(a, e.type, e.stateNode) : If(a, r, e.memoizedProps));
				}
				break;
			case 27:
				ml(t, e), _l(e), r & 512 && ($c || n === null || Wc(n, n.return)), n !== null && r & 4 && Kc(e, e.memoizedProps, n.memoizedProps);
				break;
			case 5:
				if (ml(t, e), _l(e), r & 512 && ($c || n === null || Wc(n, n.return)), e.flags & 32) {
					a = e.stateNode;
					try {
						Xt(a, "");
					} catch (t) {
						Z(e, e.return, t);
					}
				}
				r & 4 && e.stateNode != null && (a = e.memoizedProps, Kc(e, a, n === null ? a : n.memoizedProps)), r & 1024 && (el = !0);
				break;
			case 6:
				if (ml(t, e), _l(e), r & 4) {
					if (e.stateNode === null) throw Error(i(162));
					r = e.memoizedProps, n = e.stateNode;
					try {
						n.nodeValue = r;
					} catch (t) {
						Z(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Bf = null, a = hl, hl = gf(t.containerInfo), ml(t, e), hl = a, _l(e), r & 4 && n !== null && n.memoizedState.isDehydrated) try {
					Np(t.containerInfo);
				} catch (t) {
					Z(e, e.return, t);
				}
				el && (el = !1, vl(e));
				break;
			case 4:
				r = hl, hl = gf(e.stateNode.containerInfo), ml(t, e), _l(e), hl = r;
				break;
			case 12:
				ml(t, e), _l(e);
				break;
			case 31:
				ml(t, e), _l(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, pl(e, r)));
				break;
			case 13:
				ml(t, e), _l(e), e.child.flags & 8192 && e.memoizedState !== null != (n !== null && n.memoizedState !== null) && ($l = Ae()), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, pl(e, r)));
				break;
			case 22:
				a = e.memoizedState !== null;
				var l = n !== null && n.memoizedState !== null, u = Qc, d = $c;
				if (Qc = u || a, $c = d || l, ml(t, e), $c = d, Qc = u, _l(e), r & 8192) a: for (t = e.stateNode, t._visibility = a ? t._visibility & -2 : t._visibility | 1, a && (n === null || l || Qc || $c || bl(e)), n = null, t = e;;) {
					if (t.tag === 5 || t.tag === 26) {
						if (n === null) {
							l = n = t;
							try {
								if (o = l.stateNode, a) s = o.style, typeof s.setProperty == "function" ? s.setProperty("display", "none", "important") : s.display = "none";
								else {
									c = l.stateNode;
									var f = l.memoizedProps.style, p = f != null && f.hasOwnProperty("display") ? f.display : null;
									c.style.display = p == null || typeof p == "boolean" ? "" : ("" + p).trim();
								}
							} catch (e) {
								Z(l, l.return, e);
							}
						}
					} else if (t.tag === 6) {
						if (n === null) {
							l = t;
							try {
								l.stateNode.nodeValue = a ? "" : l.memoizedProps;
							} catch (e) {
								Z(l, l.return, e);
							}
						}
					} else if (t.tag === 18) {
						if (n === null) {
							l = t;
							try {
								var m = l.stateNode;
								a ? $d(m, !0) : $d(l.stateNode, !1);
							} catch (e) {
								Z(l, l.return, e);
							}
						}
					} else if ((t.tag !== 22 && t.tag !== 23 || t.memoizedState === null || t === e) && t.child !== null) {
						t.child.return = t, t = t.child;
						continue;
					}
					if (t === e) break a;
					for (; t.sibling === null;) {
						if (t.return === null || t.return === e) break a;
						n === t && (n = null), t = t.return;
					}
					n === t && (n = null), t.sibling.return = t.return, t = t.sibling;
				}
				r & 4 && (r = e.updateQueue, r !== null && (n = r.retryQueue, n !== null && (r.retryQueue = null, pl(e, n))));
				break;
			case 19:
				ml(t, e), _l(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, pl(e, r)));
				break;
			case 30: break;
			case 21: break;
			default: ml(t, e), _l(e);
		}
	}
	function _l(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				for (var n, r = e.return; r !== null;) {
					if (qc(r)) {
						n = r;
						break;
					}
					r = r.return;
				}
				if (n == null) throw Error(i(160));
				switch (n.tag) {
					case 27:
						var a = n.stateNode;
						Xc(e, Jc(e), a);
						break;
					case 5:
						var o = n.stateNode;
						n.flags & 32 && (Xt(o, ""), n.flags &= -33), Xc(e, Jc(e), o);
						break;
					case 3:
					case 4:
						var s = n.stateNode.containerInfo;
						Yc(e, Jc(e), s);
						break;
					default: throw Error(i(161));
				}
			} catch (t) {
				Z(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function vl(e) {
		if (e.subtreeFlags & 1024) for (e = e.child; e !== null;) {
			var t = e;
			vl(t), t.tag === 5 && t.flags & 1024 && t.stateNode.reset(), e = e.sibling;
		}
	}
	function yl(e, t) {
		if (t.subtreeFlags & 8772) for (t = t.child; t !== null;) il(e, t.alternate, t), t = t.sibling;
	}
	function bl(e) {
		for (e = e.child; e !== null;) {
			var t = e;
			switch (t.tag) {
				case 0:
				case 11:
				case 14:
				case 15:
					Bc(4, t, t.return), bl(t);
					break;
				case 1:
					Wc(t, t.return);
					var n = t.stateNode;
					typeof n.componentWillUnmount == "function" && Hc(t, t.return, n), bl(t);
					break;
				case 27: pf(t.stateNode);
				case 26:
				case 5:
					Wc(t, t.return), bl(t);
					break;
				case 22:
					t.memoizedState === null && bl(t);
					break;
				case 30:
					bl(t);
					break;
				default: bl(t);
			}
			e = e.sibling;
		}
	}
	function xl(e, t, n) {
		for (n = n && !!(t.subtreeFlags & 8772), t = t.child; t !== null;) {
			var r = t.alternate, i = e, a = t, o = a.flags;
			switch (a.tag) {
				case 0:
				case 11:
				case 15:
					xl(i, a, n), zc(4, a);
					break;
				case 1:
					if (xl(i, a, n), r = a, i = r.stateNode, typeof i.componentDidMount == "function") try {
						i.componentDidMount();
					} catch (e) {
						Z(r, r.return, e);
					}
					if (r = a, i = r.updateQueue, i !== null) {
						var s = r.stateNode;
						try {
							var c = i.shared.hiddenCallbacks;
							if (c !== null) for (i.shared.hiddenCallbacks = null, i = 0; i < c.length; i++) Ga(c[i], s);
						} catch (e) {
							Z(r, r.return, e);
						}
					}
					n && o & 64 && Vc(a), Uc(a, a.return);
					break;
				case 27: Zc(a);
				case 26:
				case 5:
					xl(i, a, n), n && r === null && o & 4 && Gc(a), Uc(a, a.return);
					break;
				case 12:
					xl(i, a, n);
					break;
				case 31:
					xl(i, a, n), n && o & 4 && ul(i, a);
					break;
				case 13:
					xl(i, a, n), n && o & 4 && dl(i, a);
					break;
				case 22:
					a.memoizedState === null && xl(i, a, n), Uc(a, a.return);
					break;
				case 30: break;
				default: xl(i, a, n);
			}
			t = t.sibling;
		}
	}
	function Sl(e, t) {
		var n = null;
		e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== n && (e != null && e.refCount++, n != null && ca(n));
	}
	function Cl(e, t) {
		e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ca(e));
	}
	function wl(e, t, n, r) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) Tl(e, t, n, r), t = t.sibling;
	}
	function Tl(e, t, n, r) {
		var i = t.flags;
		switch (t.tag) {
			case 0:
			case 11:
			case 15:
				wl(e, t, n, r), i & 2048 && zc(9, t);
				break;
			case 1:
				wl(e, t, n, r);
				break;
			case 3:
				wl(e, t, n, r), i & 2048 && (e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ca(e)));
				break;
			case 12:
				if (i & 2048) {
					wl(e, t, n, r), e = t.stateNode;
					try {
						var a = t.memoizedProps, o = a.id, s = a.onPostCommit;
						typeof s == "function" && s(o, t.alternate === null ? "mount" : "update", e.passiveEffectDuration, -0);
					} catch (e) {
						Z(t, t.return, e);
					}
				} else wl(e, t, n, r);
				break;
			case 31:
				wl(e, t, n, r);
				break;
			case 13:
				wl(e, t, n, r);
				break;
			case 23: break;
			case 22:
				a = t.stateNode, o = t.alternate, t.memoizedState === null ? a._visibility & 2 ? wl(e, t, n, r) : (a._visibility |= 2, El(e, t, n, r, !!(t.subtreeFlags & 10256) || !1)) : a._visibility & 2 ? wl(e, t, n, r) : Dl(e, t), i & 2048 && Sl(o, t);
				break;
			case 24:
				wl(e, t, n, r), i & 2048 && Cl(t.alternate, t);
				break;
			default: wl(e, t, n, r);
		}
	}
	function El(e, t, n, r, i) {
		for (i = i && (!!(t.subtreeFlags & 10256) || !1), t = t.child; t !== null;) {
			var a = e, o = t, s = n, c = r, l = o.flags;
			switch (o.tag) {
				case 0:
				case 11:
				case 15:
					El(a, o, s, c, i), zc(8, o);
					break;
				case 23: break;
				case 22:
					var u = o.stateNode;
					o.memoizedState === null ? (u._visibility |= 2, El(a, o, s, c, i)) : u._visibility & 2 ? El(a, o, s, c, i) : Dl(a, o), i && l & 2048 && Sl(o.alternate, o);
					break;
				case 24:
					El(a, o, s, c, i), i && l & 2048 && Cl(o.alternate, o);
					break;
				default: El(a, o, s, c, i);
			}
			t = t.sibling;
		}
	}
	function Dl(e, t) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) {
			var n = e, r = t, i = r.flags;
			switch (r.tag) {
				case 22:
					Dl(n, r), i & 2048 && Sl(r.alternate, r);
					break;
				case 24:
					Dl(n, r), i & 2048 && Cl(r.alternate, r);
					break;
				default: Dl(n, r);
			}
			t = t.sibling;
		}
	}
	var Ol = 8192;
	function kl(e, t, n) {
		if (e.subtreeFlags & Ol) for (e = e.child; e !== null;) Al(e, t, n), e = e.sibling;
	}
	function Al(e, t, n) {
		switch (e.tag) {
			case 26:
				kl(e, t, n), e.flags & Ol && e.memoizedState !== null && Gf(n, hl, e.memoizedState, e.memoizedProps);
				break;
			case 5:
				kl(e, t, n);
				break;
			case 3:
			case 4:
				var r = hl;
				hl = gf(e.stateNode.containerInfo), kl(e, t, n), hl = r;
				break;
			case 22:
				e.memoizedState === null && (r = e.alternate, r !== null && r.memoizedState !== null ? (r = Ol, Ol = 16777216, kl(e, t, n), Ol = r) : kl(e, t, n));
				break;
			default: kl(e, t, n);
		}
	}
	function jl(e) {
		var t = e.alternate;
		if (t !== null && (e = t.child, e !== null)) {
			t.child = null;
			do
				t = e.sibling, e.sibling = null, e = t;
			while (e !== null);
		}
	}
	function Ml(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				nl = r, Fl(r, e);
			}
			jl(e);
		}
		if (e.subtreeFlags & 10256) for (e = e.child; e !== null;) Nl(e), e = e.sibling;
	}
	function Nl(e) {
		switch (e.tag) {
			case 0:
			case 11:
			case 15:
				Ml(e), e.flags & 2048 && Bc(9, e, e.return);
				break;
			case 3:
				Ml(e);
				break;
			case 12:
				Ml(e);
				break;
			case 22:
				var t = e.stateNode;
				e.memoizedState !== null && t._visibility & 2 && (e.return === null || e.return.tag !== 13) ? (t._visibility &= -3, Pl(e)) : Ml(e);
				break;
			default: Ml(e);
		}
	}
	function Pl(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				nl = r, Fl(r, e);
			}
			jl(e);
		}
		for (e = e.child; e !== null;) {
			switch (t = e, t.tag) {
				case 0:
				case 11:
				case 15:
					Bc(8, t, t.return), Pl(t);
					break;
				case 22:
					n = t.stateNode, n._visibility & 2 && (n._visibility &= -3, Pl(t));
					break;
				default: Pl(t);
			}
			e = e.sibling;
		}
	}
	function Fl(e, t) {
		for (; nl !== null;) {
			var n = nl;
			switch (n.tag) {
				case 0:
				case 11:
				case 15:
					Bc(8, n, t);
					break;
				case 23:
				case 22:
					if (n.memoizedState !== null && n.memoizedState.cachePool !== null) {
						var r = n.memoizedState.cachePool.pool;
						r != null && r.refCount++;
					}
					break;
				case 24: ca(n.memoizedState.cache);
			}
			if (r = n.child, r !== null) r.return = n, nl = r;
			else a: for (n = e; nl !== null;) {
				r = nl;
				var i = r.sibling, a = r.return;
				if (al(r), r === n) {
					nl = null;
					break a;
				}
				if (i !== null) {
					i.return = a, nl = i;
					break a;
				}
				nl = a;
			}
		}
	}
	var Il = {
		getCacheForType: function(e) {
			var t = z(sa), n = t.data.get(e);
			return n === void 0 && (n = e(), t.data.set(e, n)), n;
		},
		cacheSignal: function() {
			return z(sa).controller.signal;
		}
	}, Ll = typeof WeakMap == "function" ? WeakMap : Map, q = 0, Rl = null, J = null, Y = 0, X = 0, zl = null, Bl = !1, Vl = !1, Hl = !1, Ul = 0, Wl = 0, Gl = 0, Kl = 0, ql = 0, Jl = 0, Yl = 0, Xl = null, Zl = null, Ql = !1, $l = 0, eu = 0, tu = Infinity, nu = null, ru = null, iu = 0, au = null, ou = null, su = 0, cu = 0, lu = null, uu = null, du = 0, fu = null;
	function pu() {
		return q & 2 && Y !== 0 ? Y & -Y : j.T === null ? ct() : dd();
	}
	function mu() {
		if (Jl === 0) {
			if (!(Y & 536870912) || R) {
				var e = qe;
				qe <<= 1, !(qe & 3932160) && (qe = 262144), Jl = e;
			} else Jl = 536870912;
		}
		return e = Qa.current, e !== null && (e.flags |= 32), Jl;
	}
	function hu(e, t, n) {
		(e === Rl && (X === 2 || X === 9) || e.cancelPendingCommit !== null) && (Su(e, 0), yu(e, Y, Jl, !1)), tt(e, n), (!(q & 2) || e !== Rl) && (e === Rl && (!(q & 2) && (Kl |= n), Wl === 4 && yu(e, Y, Jl, !1)), rd(e));
	}
	function gu(e, t, n) {
		if (q & 6) throw Error(i(327));
		var r = !n && !(t & 127) && (t & e.expiredLanes) === 0 || Ze(e, t), a = r ? Au(e, t) : Ou(e, t, !0), o = r;
		do {
			if (a === 0) {
				Vl && !r && yu(e, t, 0, !1);
				break;
			}
			if (n = e.current.alternate, o && !vu(n)) {
				a = Ou(e, t, !1), o = !1;
				continue;
			}
			if (a === 2) {
				if (o = t, e.errorRecoveryDisabledLanes & o) var s = 0;
				else s = e.pendingLanes & -536870913, s = s === 0 ? s & 536870912 ? 536870912 : 0 : s;
				if (s !== 0) {
					t = s;
					a: {
						var c = e;
						a = Xl;
						var l = c.current.memoizedState.isDehydrated;
						if (l && (Su(c, s).flags |= 256), s = Ou(c, s, !1), s !== 2) {
							if (Hl && !l) {
								c.errorRecoveryDisabledLanes |= o, Kl |= o, a = 4;
								break a;
							}
							o = Zl, Zl = a, o !== null && (Zl === null ? Zl = o : Zl.push.apply(Zl, o));
						}
						a = s;
					}
					if (o = !1, a !== 2) continue;
				}
			}
			if (a === 1) {
				Su(e, 0), yu(e, t, 0, !0);
				break;
			}
			a: {
				switch (r = e, o = a, o) {
					case 0:
					case 1: throw Error(i(345));
					case 4: if ((t & 4194048) !== t) break;
					case 6:
						yu(r, t, Jl, !Bl);
						break a;
					case 2:
						Zl = null;
						break;
					case 3:
					case 5: break;
					default: throw Error(i(329));
				}
				if ((t & 62914560) === t && (a = $l + 300 - Ae(), 10 < a)) {
					if (yu(r, t, Jl, !Bl), Xe(r, 0, !0) !== 0) break a;
					su = t, r.timeoutHandle = Kd(_u.bind(null, r, n, Zl, nu, Ql, t, Jl, Kl, Yl, Bl, o, "Throttled", -0, 0), a);
					break a;
				}
				_u(r, n, Zl, nu, Ql, t, Jl, Kl, Yl, Bl, o, null, -0, 0);
			}
			break;
		} while (1);
		rd(e);
	}
	function _u(e, t, n, r, i, a, o, s, c, l, u, d, f, p) {
		if (e.timeoutHandle = -1, d = t.subtreeFlags, d & 8192 || (d & 16785408) == 16785408) {
			d = {
				stylesheets: null,
				count: 0,
				imgCount: 0,
				imgBytes: 0,
				suspenseyImages: [],
				waitingForImages: !0,
				waitingForViewTransition: !1,
				unsuspend: an
			}, Al(t, a, d);
			var m = (a & 62914560) === a ? $l - Ae() : (a & 4194048) === a ? eu - Ae() : 0;
			if (m = qf(d, m), m !== null) {
				su = a, e.cancelPendingCommit = m(Lu.bind(null, e, t, a, n, r, i, o, s, c, u, d, null, f, p)), yu(e, a, o, !l);
				return;
			}
		}
		Lu(e, t, a, n, r, i, o, s, c);
	}
	function vu(e) {
		for (var t = e;;) {
			var n = t.tag;
			if ((n === 0 || n === 11 || n === 15) && t.flags & 16384 && (n = t.updateQueue, n !== null && (n = n.stores, n !== null))) for (var r = 0; r < n.length; r++) {
				var i = n[r], a = i.getSnapshot;
				i = i.value;
				try {
					if (!wr(a(), i)) return !1;
				} catch {
					return !1;
				}
			}
			if (n = t.child, t.subtreeFlags & 16384 && n !== null) n.return = t, t = n;
			else {
				if (t === e) break;
				for (; t.sibling === null;) {
					if (t.return === null || t.return === e) return !0;
					t = t.return;
				}
				t.sibling.return = t.return, t = t.sibling;
			}
		}
		return !0;
	}
	function yu(e, t, n, r) {
		t &= ~ql, t &= ~Kl, e.suspendedLanes |= t, e.pingedLanes &= ~t, r && (e.warmLanes |= t), r = e.expirationTimes;
		for (var i = t; 0 < i;) {
			var a = 31 - He(i), o = 1 << a;
			r[a] = -1, i &= ~o;
		}
		n !== 0 && rt(e, n, t);
	}
	function bu() {
		return q & 6 ? !0 : (id(0, !1), !1);
	}
	function xu() {
		if (J !== null) {
			if (X === 0) var e = J.return;
			else e = J, Ji = qi = null, To(e), Da = null, Oa = 0, e = J;
			for (; e !== null;) Rc(e.alternate, e), e = e.return;
			J = null;
		}
	}
	function Su(e, t) {
		var n = e.timeoutHandle;
		n !== -1 && (e.timeoutHandle = -1, qd(n)), n = e.cancelPendingCommit, n !== null && (e.cancelPendingCommit = null, n()), su = 0, xu(), Rl = e, J = n = fi(e.current, null), Y = t, X = 0, zl = null, Bl = !1, Vl = Ze(e, t), Hl = !1, Yl = Jl = ql = Kl = Gl = Wl = 0, Zl = Xl = null, Ql = !1, t & 8 && (t |= t & 32);
		var r = e.entangledLanes;
		if (r !== 0) for (e = e.entanglements, r &= t; 0 < r;) {
			var i = 31 - He(r), a = 1 << i;
			t |= e[i], r &= ~a;
		}
		return Ul = t, ni(), n;
	}
	function Cu(e, t) {
		G = null, j.H = Fs, t === ya || t === W ? (t = Ta(), X = 3) : t === U ? (t = Ta(), X = 4) : X = t === $s ? 8 : typeof t == "object" && t && typeof t.then == "function" ? 6 : 1, zl = t, J === null && (Wl = 1, qs(e, bi(t, e.current)));
	}
	function wu() {
		var e = Qa.current;
		return e === null ? !0 : (Y & 4194048) === Y ? $a === null : (Y & 62914560) === Y || Y & 536870912 ? e === $a : !1;
	}
	function Tu() {
		var e = j.H;
		return j.H = Fs, e === null ? Fs : e;
	}
	function Eu() {
		var e = j.A;
		return j.A = Il, e;
	}
	function Du() {
		Wl = 4, Bl || (Y & 4194048) !== Y && Qa.current !== null || (Vl = !0), !(Gl & 134217727) && !(Kl & 134217727) || Rl === null || yu(Rl, Y, Jl, !1);
	}
	function Ou(e, t, n) {
		var r = q;
		q |= 2;
		var i = Tu(), a = Eu();
		(Rl !== e || Y !== t) && (nu = null, Su(e, t)), t = !1;
		var o = Wl;
		a: do
			try {
				if (X !== 0 && J !== null) {
					var s = J, c = zl;
					switch (X) {
						case 8:
							xu(), o = 6;
							break a;
						case 3:
						case 2:
						case 9:
						case 6:
							Qa.current === null && (t = !0);
							var l = X;
							if (X = 0, zl = null, Pu(e, s, c, l), n && Vl) {
								o = 0;
								break a;
							}
							break;
						default: l = X, X = 0, zl = null, Pu(e, s, c, l);
					}
				}
				ku(), o = Wl;
				break;
			} catch (t) {
				Cu(e, t);
			}
		while (1);
		return t && e.shellSuspendCounter++, Ji = qi = null, q = r, j.H = i, j.A = a, J === null && (Rl = null, Y = 0, ni()), o;
	}
	function ku() {
		for (; J !== null;) Mu(J);
	}
	function Au(e, t) {
		var n = q;
		q |= 2;
		var r = Tu(), a = Eu();
		Rl !== e || Y !== t ? (nu = null, tu = Ae() + 500, Su(e, t)) : Vl = Ze(e, t);
		a: do
			try {
				if (X !== 0 && J !== null) {
					t = J;
					var o = zl;
					b: switch (X) {
						case 1:
							X = 0, zl = null, Pu(e, t, o, 1);
							break;
						case 2:
						case 9:
							if (xa(o)) {
								X = 0, zl = null, Nu(t);
								break;
							}
							t = function() {
								X !== 2 && X !== 9 || Rl !== e || (X = 7), rd(e);
							}, o.then(t, t);
							break a;
						case 3:
							X = 7;
							break a;
						case 4:
							X = 5;
							break a;
						case 7:
							xa(o) ? (X = 0, zl = null, Nu(t)) : (X = 0, zl = null, Pu(e, t, o, 7));
							break;
						case 5:
							var s = null;
							switch (J.tag) {
								case 26: s = J.memoizedState;
								case 5:
								case 27:
									var c = J;
									if (s ? Wf(s) : c.stateNode.complete) {
										X = 0, zl = null;
										var l = c.sibling;
										if (l !== null) J = l;
										else {
											var u = c.return;
											u === null ? J = null : (J = u, Fu(u));
										}
										break b;
									}
							}
							X = 0, zl = null, Pu(e, t, o, 5);
							break;
						case 6:
							X = 0, zl = null, Pu(e, t, o, 6);
							break;
						case 8:
							xu(), Wl = 6;
							break a;
						default: throw Error(i(462));
					}
				}
				ju();
				break;
			} catch (t) {
				Cu(e, t);
			}
		while (1);
		return Ji = qi = null, j.H = r, j.A = a, q = n, J === null ? (Rl = null, Y = 0, ni(), Wl) : 0;
	}
	function ju() {
		for (; J !== null && !Oe();) Mu(J);
	}
	function Mu(e) {
		var t = kc(e.alternate, e, Ul);
		e.memoizedProps = e.pendingProps, t === null ? Fu(e) : J = t;
	}
	function Nu(e) {
		var t = e, n = t.alternate;
		switch (t.tag) {
			case 15:
			case 0:
				t = pc(n, t, t.pendingProps, t.type, void 0, Y);
				break;
			case 11:
				t = pc(n, t, t.pendingProps, t.type.render, t.ref, Y);
				break;
			case 5: To(t);
			default: Rc(n, t), t = J = pi(t, Ul), t = kc(n, t, Ul);
		}
		e.memoizedProps = e.pendingProps, t === null ? Fu(e) : J = t;
	}
	function Pu(e, t, n, r) {
		Ji = qi = null, To(t), Da = null, Oa = 0;
		var i = t.return;
		try {
			if (Qs(e, i, t, n, Y)) {
				Wl = 1, qs(e, bi(n, e.current)), J = null;
				return;
			}
		} catch (t) {
			if (i !== null) throw J = i, t;
			Wl = 1, qs(e, bi(n, e.current)), J = null;
			return;
		}
		t.flags & 32768 ? (R || r === 1 ? e = !0 : Vl || Y & 536870912 ? e = !1 : (Bl = e = !0, (r === 2 || r === 9 || r === 3 || r === 6) && (r = Qa.current, r !== null && r.tag === 13 && (r.flags |= 16384))), Iu(t, e)) : Fu(t);
	}
	function Fu(e) {
		var t = e;
		do {
			if (t.flags & 32768) {
				Iu(t, Bl);
				return;
			}
			e = t.return;
			var n = Ic(t.alternate, t, Ul);
			if (n !== null) {
				J = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				J = t;
				return;
			}
			J = t = e;
		} while (t !== null);
		Wl === 0 && (Wl = 5);
	}
	function Iu(e, t) {
		do {
			var n = Lc(e.alternate, e);
			if (n !== null) {
				n.flags &= 32767, J = n;
				return;
			}
			if (n = e.return, n !== null && (n.flags |= 32768, n.subtreeFlags = 0, n.deletions = null), !t && (e = e.sibling, e !== null)) {
				J = e;
				return;
			}
			J = e = n;
		} while (e !== null);
		Wl = 6, J = null;
	}
	function Lu(e, t, n, r, a, o, s, c, l) {
		e.cancelPendingCommit = null;
		do
			Hu();
		while (iu !== 0);
		if (q & 6) throw Error(i(327));
		if (t !== null) {
			if (t === e.current) throw Error(i(177));
			if (o = t.lanes | t.childLanes, o |= ti, nt(e, n, o, s, c, l), e === Rl && (J = Rl = null, Y = 0), ou = t, au = e, su = n, cu = o, lu = a, uu = r, t.subtreeFlags & 10256 || t.flags & 10256 ? (e.callbackNode = null, e.callbackPriority = 0, Xu(Pe, function() {
				return Uu(), null;
			})) : (e.callbackNode = null, e.callbackPriority = 0), r = !!(t.flags & 13878), t.subtreeFlags & 13878 || r) {
				r = j.T, j.T = null, a = M.p, M.p = 2, s = q, q |= 4;
				try {
					rl(e, t, n);
				} finally {
					q = s, M.p = a, j.T = r;
				}
			}
			iu = 1, Ru(), zu(), Bu();
		}
	}
	function Ru() {
		if (iu === 1) {
			iu = 0;
			var e = au, t = ou, n = !!(t.flags & 13878);
			if (t.subtreeFlags & 13878 || n) {
				n = j.T, j.T = null;
				var r = M.p;
				M.p = 2;
				var i = q;
				q |= 4;
				try {
					gl(t, e);
					var a = zd, o = kr(e.containerInfo), s = a.focusedElem, c = a.selectionRange;
					if (o !== s && s && s.ownerDocument && Or(s.ownerDocument.documentElement, s)) {
						if (c !== null && Ar(s)) {
							var l = c.start, u = c.end;
							if (u === void 0 && (u = l), "selectionStart" in s) s.selectionStart = l, s.selectionEnd = Math.min(u, s.value.length);
							else {
								var d = s.ownerDocument || document, f = d && d.defaultView || window;
								if (f.getSelection) {
									var p = f.getSelection(), m = s.textContent.length, h = Math.min(c.start, m), g = c.end === void 0 ? h : Math.min(c.end, m);
									!p.extend && h > g && (o = g, g = h, h = o);
									var _ = Dr(s, h), v = Dr(s, g);
									if (_ && v && (p.rangeCount !== 1 || p.anchorNode !== _.node || p.anchorOffset !== _.offset || p.focusNode !== v.node || p.focusOffset !== v.offset)) {
										var y = d.createRange();
										y.setStart(_.node, _.offset), p.removeAllRanges(), h > g ? (p.addRange(y), p.extend(v.node, v.offset)) : (y.setEnd(v.node, v.offset), p.addRange(y));
									}
								}
							}
						}
						for (d = [], p = s; p = p.parentNode;) p.nodeType === 1 && d.push({
							element: p,
							left: p.scrollLeft,
							top: p.scrollTop
						});
						for (typeof s.focus == "function" && s.focus(), s = 0; s < d.length; s++) {
							var b = d[s];
							b.element.scrollLeft = b.left, b.element.scrollTop = b.top;
						}
					}
					sp = !!Rd, zd = Rd = null;
				} finally {
					q = i, M.p = r, j.T = n;
				}
			}
			e.current = t, iu = 2;
		}
	}
	function zu() {
		if (iu === 2) {
			iu = 0;
			var e = au, t = ou, n = !!(t.flags & 8772);
			if (t.subtreeFlags & 8772 || n) {
				n = j.T, j.T = null;
				var r = M.p;
				M.p = 2;
				var i = q;
				q |= 4;
				try {
					il(e, t.alternate, t);
				} finally {
					q = i, M.p = r, j.T = n;
				}
			}
			iu = 3;
		}
	}
	function Bu() {
		if (iu === 4 || iu === 3) {
			iu = 0, ke();
			var e = au, t = ou, n = su, r = uu;
			t.subtreeFlags & 10256 || t.flags & 10256 ? iu = 5 : (iu = 0, ou = au = null, Vu(e, e.pendingLanes));
			var i = e.pendingLanes;
			if (i === 0 && (ru = null), st(n), t = t.stateNode, Be && typeof Be.onCommitFiberRoot == "function") try {
				Be.onCommitFiberRoot(ze, t, void 0, (t.current.flags & 128) == 128);
			} catch {}
			if (r !== null) {
				t = j.T, i = M.p, M.p = 2, j.T = null;
				try {
					for (var a = e.onRecoverableError, o = 0; o < r.length; o++) {
						var s = r[o];
						a(s.value, { componentStack: s.stack });
					}
				} finally {
					j.T = t, M.p = i;
				}
			}
			su & 3 && Hu(), rd(e), i = e.pendingLanes, n & 261930 && i & 42 ? e === fu ? du++ : (du = 0, fu = e) : du = 0, id(0, !1);
		}
	}
	function Vu(e, t) {
		(e.pooledCacheLanes &= t) === 0 && (t = e.pooledCache, t != null && (e.pooledCache = null, ca(t)));
	}
	function Hu() {
		return Ru(), zu(), Bu(), Uu();
	}
	function Uu() {
		if (iu !== 5) return !1;
		var e = au, t = cu;
		cu = 0;
		var n = st(su), r = j.T, a = M.p;
		try {
			M.p = 32 > n ? 32 : n, j.T = null, n = lu, lu = null;
			var o = au, s = su;
			if (iu = 0, ou = au = null, su = 0, q & 6) throw Error(i(331));
			var c = q;
			if (q |= 4, Nl(o.current), Tl(o, o.current, s, n), q = c, id(0, !1), Be && typeof Be.onPostCommitFiberRoot == "function") try {
				Be.onPostCommitFiberRoot(ze, o);
			} catch {}
			return !0;
		} finally {
			M.p = a, j.T = r, Vu(e, t);
		}
	}
	function Wu(e, t, n) {
		t = bi(n, t), t = Ys(e.stateNode, t, 2), e = za(e, t, 2), e !== null && (tt(e, 2), rd(e));
	}
	function Z(e, t, n) {
		if (e.tag === 3) Wu(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Wu(t, e, n);
				break;
			}
			if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (ru === null || !ru.has(r))) {
					e = bi(n, e), n = Xs(2), r = za(t, n, 2), r !== null && (Zs(n, r, t, e), tt(r, 2), rd(r));
					break;
				}
			}
			t = t.return;
		}
	}
	function Gu(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Ll();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (Hl = !0, i.add(n), e = Ku.bind(null, e, t, n), t.then(e, e));
	}
	function Ku(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), e.pingedLanes |= e.suspendedLanes & n, e.warmLanes &= ~n, Rl === e && (Y & n) === n && (Wl === 4 || Wl === 3 && (Y & 62914560) === Y && 300 > Ae() - $l ? !(q & 2) && Su(e, 0) : ql |= n, Yl === Y && (Yl = 0)), rd(e);
	}
	function qu(e, t) {
		t === 0 && (t = $e()), e = ai(e, t), e !== null && (tt(e, t), rd(e));
	}
	function Ju(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), qu(e, n);
	}
	function Yu(e, t) {
		var n = 0;
		switch (e.tag) {
			case 31:
			case 13:
				var r = e.stateNode, a = e.memoizedState;
				a !== null && (n = a.retryLane);
				break;
			case 19:
				r = e.stateNode;
				break;
			case 22:
				r = e.stateNode._retryCache;
				break;
			default: throw Error(i(314));
		}
		r !== null && r.delete(t), qu(e, n);
	}
	function Xu(e, t) {
		return Ee(e, t);
	}
	var Zu = null, Qu = null, $u = !1, ed = !1, td = !1, nd = 0;
	function rd(e) {
		e !== Qu && e.next === null && (Qu === null ? Zu = Qu = e : Qu = Qu.next = e), ed = !0, $u || ($u = !0, ud());
	}
	function id(e, t) {
		if (!td && ed) {
			td = !0;
			do
				for (var n = !1, r = Zu; r !== null;) {
					if (!t) {
						if (e !== 0) {
							var i = r.pendingLanes;
							if (i === 0) var a = 0;
							else {
								var o = r.suspendedLanes, s = r.pingedLanes;
								a = (1 << 31 - He(42 | e) + 1) - 1, a &= i & ~(o & ~s), a = a & 201326741 ? a & 201326741 | 1 : a ? a | 2 : 0;
							}
							a !== 0 && (n = !0, ld(r, a));
						} else a = Y, a = Xe(r, r === Rl ? a : 0, r.cancelPendingCommit !== null || r.timeoutHandle !== -1), !(a & 3) || Ze(r, a) || (n = !0, ld(r, a));
					}
					r = r.next;
				}
			while (n);
			td = !1;
		}
	}
	function ad() {
		od();
	}
	function od() {
		ed = $u = !1;
		var e = 0;
		nd !== 0 && Gd() && (e = nd);
		for (var t = Ae(), n = null, r = Zu; r !== null;) {
			var i = r.next, a = sd(r, t);
			a === 0 ? (r.next = null, n === null ? Zu = i : n.next = i, i === null && (Qu = n)) : (n = r, (e !== 0 || a & 3) && (ed = !0)), r = i;
		}
		iu !== 0 && iu !== 5 || id(e, !1), nd !== 0 && (nd = 0);
	}
	function sd(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes & -62914561; 0 < a;) {
			var o = 31 - He(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = Qe(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
		if (t = Rl, n = Y, n = Xe(e, e === t ? n : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r = e.callbackNode, n === 0 || e === t && (X === 2 || X === 9) || e.cancelPendingCommit !== null) return r !== null && r !== null && De(r), e.callbackNode = null, e.callbackPriority = 0;
		if (!(n & 3) || Ze(e, n)) {
			if (t = n & -n, t === e.callbackPriority) return t;
			switch (r !== null && De(r), st(n)) {
				case 2:
				case 8:
					n = Ne;
					break;
				case 32:
					n = Pe;
					break;
				case 268435456:
					n = Ie;
					break;
				default: n = Pe;
			}
			return r = cd.bind(null, e), n = Ee(n, r), e.callbackPriority = t, e.callbackNode = n, t;
		}
		return r !== null && r !== null && De(r), e.callbackPriority = 2, e.callbackNode = null, 2;
	}
	function cd(e, t) {
		if (iu !== 0 && iu !== 5) return e.callbackNode = null, e.callbackPriority = 0, null;
		var n = e.callbackNode;
		if (Hu() && e.callbackNode !== n) return null;
		var r = Y;
		return r = Xe(e, e === Rl ? r : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r === 0 ? null : (gu(e, r, t), sd(e, Ae()), e.callbackNode != null && e.callbackNode === n ? cd.bind(null, e) : null);
	}
	function ld(e, t) {
		if (Hu()) return null;
		gu(e, t, !0);
	}
	function ud() {
		Yd(function() {
			q & 6 ? Ee(Me, ad) : od();
		});
	}
	function dd() {
		if (nd === 0) {
			var e = da;
			e === 0 && (e = Ke, Ke <<= 1, !(Ke & 261888) && (Ke = 256)), nd = e;
		}
		return nd;
	}
	function fd(e) {
		return e == null || typeof e == "symbol" || typeof e == "boolean" ? null : typeof e == "function" ? e : rn("" + e);
	}
	function pd(e, t) {
		var n = t.ownerDocument.createElement("input");
		return n.name = t.name, n.value = t.value, e.id && n.setAttribute("form", e.id), t.parentNode.insertBefore(n, t), e = new FormData(e), n.parentNode.removeChild(n), e;
	}
	function md(e, t, n, r, i) {
		if (t === "submit" && n && n.stateNode === i) {
			var a = fd((i[ft] || null).action), o = r.submitter;
			o && (t = (t = o[ft] || null) ? fd(t.formAction) : o.getAttribute("formAction"), t !== null && (a = t, o = null));
			var s = new En("action", "action", null, r, i);
			e.push({
				event: s,
				listeners: [{
					instance: null,
					listener: function() {
						if (r.defaultPrevented) {
							if (nd !== 0) {
								var e = o ? pd(i, o) : new FormData(i);
								xs(n, {
									pending: !0,
									data: e,
									method: i.method,
									action: a
								}, null, e);
							}
						} else typeof a == "function" && (s.preventDefault(), e = o ? pd(i, o) : new FormData(i), xs(n, {
							pending: !0,
							data: e,
							method: i.method,
							action: a
						}, a, e));
					},
					currentTarget: i
				}]
			});
		}
	}
	for (var hd = 0; hd < Xr.length; hd++) {
		var gd = Xr[hd];
		Zr(gd.toLowerCase(), "on" + (gd[0].toUpperCase() + gd.slice(1)));
	}
	Zr(Hr, "onAnimationEnd"), Zr(Ur, "onAnimationIteration"), Zr(Wr, "onAnimationStart"), Zr("dblclick", "onDoubleClick"), Zr("focusin", "onFocus"), Zr("focusout", "onBlur"), Zr(Gr, "onTransitionRun"), Zr(Kr, "onTransitionStart"), Zr(qr, "onTransitionCancel"), Zr(Jr, "onTransitionEnd"), Ot("onMouseEnter", ["mouseout", "mouseover"]), Ot("onMouseLeave", ["mouseout", "mouseover"]), Ot("onPointerEnter", ["pointerout", "pointerover"]), Ot("onPointerLeave", ["pointerout", "pointerover"]), Dt("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), Dt("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), Dt("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), Dt("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), Dt("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), Dt("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
	var _d = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), vd = new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(_d));
	function yd(e, t) {
		t = !!(t & 4);
		for (var n = 0; n < e.length; n++) {
			var r = e[n], i = r.event;
			r = r.listeners;
			a: {
				var a = void 0;
				if (t) for (var o = r.length - 1; 0 <= o; o--) {
					var s = r[o], c = s.instance, l = s.currentTarget;
					if (s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						Qr(e);
					}
					i.currentTarget = null, a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						Qr(e);
					}
					i.currentTarget = null, a = c;
				}
			}
		}
	}
	function Q(e, t) {
		var n = t[mt];
		n === void 0 && (n = t[mt] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (Cd(t, e, 2, !1), n.add(r));
	}
	function bd(e, t, n) {
		var r = 0;
		t && (r |= 4), Cd(n, e, r, t);
	}
	var xd = "_reactListening" + Math.random().toString(36).slice(2);
	function Sd(e) {
		if (!e[xd]) {
			e[xd] = !0, Tt.forEach(function(t) {
				t !== "selectionchange" && (vd.has(t) || bd(t, !1, e), bd(t, !0, e));
			});
			var t = e.nodeType === 9 ? e : e.ownerDocument;
			t === null || t[xd] || (t[xd] = !0, bd("selectionchange", !1, t));
		}
	}
	function Cd(e, t, n, r) {
		switch (mp(t)) {
			case 2:
				var i = cp;
				break;
			case 8:
				i = lp;
				break;
			default: i = up;
		}
		n = i.bind(null, t, n, e), i = void 0, !hn || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
			capture: !0,
			passive: i
		}) : i === void 0 ? e.addEventListener(t, n, !1) : e.addEventListener(t, n, { passive: i });
	}
	function wd(e, t, n, r, i) {
		var a = r;
		if (!(t & 1) && !(t & 2) && r !== null) a: for (;;) {
			if (r === null) return;
			var s = r.tag;
			if (s === 3 || s === 4) {
				var c = r.stateNode.containerInfo;
				if (c === i) break;
				if (s === 4) for (s = r.return; s !== null;) {
					var l = s.tag;
					if ((l === 3 || l === 4) && s.stateNode.containerInfo === i) return;
					s = s.return;
				}
				for (; c !== null;) {
					if (s = bt(c), s === null) return;
					if (l = s.tag, l === 5 || l === 6 || l === 26 || l === 27) {
						r = a = s;
						continue a;
					}
					c = c.parentNode;
				}
			}
			r = r.return;
		}
		fn(function() {
			var r = a, i = sn(n), s = [];
			a: {
				var c = Yr.get(e);
				if (c !== void 0) {
					var l = En, u = e;
					switch (e) {
						case "keypress": if (xn(n) === 0) break a;
						case "keydown":
						case "keyup":
							l = Un;
							break;
						case "focusin":
							u = "focus", l = P;
							break;
						case "focusout":
							u = "blur", l = P;
							break;
						case "beforeblur":
						case "afterblur":
							l = P;
							break;
						case "click": if (n.button === 2) break a;
						case "auxclick":
						case "dblclick":
						case "mousedown":
						case "mousemove":
						case "mouseup":
						case "mouseout":
						case "mouseover":
						case "contextmenu":
							l = Nn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							l = Pn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							l = Gn;
							break;
						case Hr:
						case Ur:
						case Wr:
							l = Fn;
							break;
						case Jr:
							l = Kn;
							break;
						case "scroll":
						case "scrollend":
							l = On;
							break;
						case "wheel":
							l = F;
							break;
						case "copy":
						case "cut":
						case "paste":
							l = In;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup":
							l = Wn;
							break;
						case "toggle":
						case "beforetoggle": l = qn;
					}
					var d = !!(t & 4), f = !d && (e === "scroll" || e === "scrollend"), p = d ? c === null ? null : c + "Capture" : c;
					d = [];
					for (var m = r, h; m !== null;) {
						var g = m;
						if (h = g.stateNode, g = g.tag, g !== 5 && g !== 26 && g !== 27 || h === null || p === null || (g = pn(m, p), g != null && d.push(Td(m, g, h))), f) break;
						m = m.return;
					}
					0 < d.length && (c = new l(c, u, null, n, i), s.push({
						event: c,
						listeners: d
					}));
				}
			}
			if (!(t & 7)) {
				a: {
					if (c = e === "mouseover" || e === "pointerover", l = e === "mouseout" || e === "pointerout", c && n !== on && (u = n.relatedTarget || n.fromElement) && (bt(u) || u[pt])) break a;
					if ((l || c) && (c = i.window === i ? i : (c = i.ownerDocument) ? c.defaultView || c.parentWindow : window, l ? (u = n.relatedTarget || n.toElement, l = r, u = u ? bt(u) : null, u !== null && (f = o(u), d = u.tag, u !== f || d !== 5 && d !== 27 && d !== 6) && (u = null)) : (l = null, u = r), l !== u)) {
						if (d = Nn, g = "onMouseLeave", p = "onMouseEnter", m = "mouse", (e === "pointerout" || e === "pointerover") && (d = Wn, g = "onPointerLeave", p = "onPointerEnter", m = "pointer"), f = l == null ? c : St(l), h = u == null ? c : St(u), c = new d(g, m + "leave", l, n, i), c.target = f, c.relatedTarget = h, g = null, bt(i) === r && (d = new d(p, m + "enter", u, n, i), d.target = h, d.relatedTarget = f, g = d), f = g, l && u) b: {
							for (d = Dd, p = l, m = u, h = 0, g = p; g; g = d(g)) h++;
							g = 0;
							for (var _ = m; _; _ = d(_)) g++;
							for (; 0 < h - g;) p = d(p), h--;
							for (; 0 < g - h;) m = d(m), g--;
							for (; h--;) {
								if (p === m || m !== null && p === m.alternate) {
									d = p;
									break b;
								}
								p = d(p), m = d(m);
							}
							d = null;
						}
						else d = null;
						l !== null && Od(s, c, l, d, !1), u !== null && f !== null && Od(s, f, u, d, !0);
					}
				}
				a: {
					if (c = r ? St(r) : window, l = c.nodeName && c.nodeName.toLowerCase(), l === "select" || l === "input" && c.type === "file") var v = fr;
					else if (sr(c)) {
						if (pr) v = Sr;
						else {
							v = br;
							var y = yr;
						}
					} else l = c.nodeName, !l || l.toLowerCase() !== "input" || c.type !== "checkbox" && c.type !== "radio" ? r && en(r.elementType) && (v = fr) : v = xr;
					if (v && (v = v(e, r))) {
						cr(s, v, n, i);
						break a;
					}
					y && y(e, c, r), e === "focusout" && r && c.type === "number" && r.memoizedProps.value != null && Kt(c, "number", c.value);
				}
				switch (y = r ? St(r) : window, e) {
					case "focusin":
						(sr(y) || y.contentEditable === "true") && (Mr = y, Nr = r, Pr = null);
						break;
					case "focusout":
						Pr = Nr = Mr = null;
						break;
					case "mousedown":
						Fr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Fr = !1, Ir(s, n, i);
						break;
					case "selectionchange": if (jr) break;
					case "keydown":
					case "keyup": Ir(s, n, i);
				}
				var b;
				if (Yn) b: {
					switch (e) {
						case "compositionstart":
							var x = "onCompositionStart";
							break b;
						case "compositionend":
							x = "onCompositionEnd";
							break b;
						case "compositionupdate":
							x = "onCompositionUpdate";
							break b;
					}
					x = void 0;
				}
				else rr ? tr(e, n) && (x = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (x = "onCompositionStart");
				x && (Qn && n.locale !== "ko" && (rr || x !== "onCompositionStart" ? x === "onCompositionEnd" && rr && (b = bn()) : (_n = i, vn = "value" in _n ? _n.value : _n.textContent, rr = !0)), y = Ed(r, x), 0 < y.length && (x = new Ln(x, e, null, n, i), s.push({
					event: x,
					listeners: y
				}), b ? x.data = b : (b = nr(n), b !== null && (x.data = b)))), (b = Zn ? ir(e, n) : ar(e, n)) && (x = Ed(r, "onBeforeInput"), 0 < x.length && (y = new Ln("onBeforeInput", "beforeinput", null, n, i), s.push({
					event: y,
					listeners: x
				}), y.data = b)), md(s, e, r, n, i);
			}
			yd(s, t);
		});
	}
	function Td(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function Ed(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			if (i = i.tag, i !== 5 && i !== 26 && i !== 27 || a === null || (i = pn(e, n), i != null && r.unshift(Td(e, i, a)), i = pn(e, t), i != null && r.push(Td(e, i, a))), e.tag === 3) return r;
			e = e.return;
		}
		return [];
	}
	function Dd(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5 && e.tag !== 27);
		return e || null;
	}
	function Od(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (s = s.tag, c !== null && c === r) break;
			s !== 5 && s !== 26 && s !== 27 || l === null || (c = l, i ? (l = pn(n, a), l != null && o.unshift(Td(n, l, c))) : i || (l = pn(n, a), l != null && o.push(Td(n, l, c)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var kd = /\r\n?/g, Ad = /\u0000|\uFFFD/g;
	function jd(e) {
		return (typeof e == "string" ? e : "" + e).replace(kd, "\n").replace(Ad, "");
	}
	function Md(e, t) {
		return t = jd(t), jd(e) === t;
	}
	function $(e, t, n, r, a, o) {
		switch (n) {
			case "children":
				typeof r == "string" ? t === "body" || t === "textarea" && r === "" || Xt(e, r) : (typeof r == "number" || typeof r == "bigint") && t !== "body" && Xt(e, "" + r);
				break;
			case "className":
				Pt(e, "class", r);
				break;
			case "tabIndex":
				Pt(e, "tabindex", r);
				break;
			case "dir":
			case "role":
			case "viewBox":
			case "width":
			case "height":
				Pt(e, n, r);
				break;
			case "style":
				$t(e, r, o);
				break;
			case "data": if (t !== "object") {
				Pt(e, "data", r);
				break;
			}
			case "src":
			case "href":
				if (r === "" && (t !== "a" || n !== "href")) {
					e.removeAttribute(n);
					break;
				}
				if (r == null || typeof r == "function" || typeof r == "symbol" || typeof r == "boolean") {
					e.removeAttribute(n);
					break;
				}
				r = rn("" + r), e.setAttribute(n, r);
				break;
			case "action":
			case "formAction":
				if (typeof r == "function") {
					e.setAttribute(n, "javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')");
					break;
				}
				if (typeof o == "function" && (n === "formAction" ? (t !== "input" && $(e, t, "name", a.name, a, null), $(e, t, "formEncType", a.formEncType, a, null), $(e, t, "formMethod", a.formMethod, a, null), $(e, t, "formTarget", a.formTarget, a, null)) : ($(e, t, "encType", a.encType, a, null), $(e, t, "method", a.method, a, null), $(e, t, "target", a.target, a, null))), r == null || typeof r == "symbol" || typeof r == "boolean") {
					e.removeAttribute(n);
					break;
				}
				r = rn("" + r), e.setAttribute(n, r);
				break;
			case "onClick":
				r != null && (e.onclick = an);
				break;
			case "onScroll":
				r != null && Q("scroll", e);
				break;
			case "onScrollEnd":
				r != null && Q("scrollend", e);
				break;
			case "dangerouslySetInnerHTML":
				if (r != null) {
					if (typeof r != "object" || !("__html" in r)) throw Error(i(61));
					if (n = r.__html, n != null) {
						if (a.children != null) throw Error(i(60));
						e.innerHTML = n;
					}
				}
				break;
			case "multiple":
				e.multiple = r && typeof r != "function" && typeof r != "symbol";
				break;
			case "muted":
				e.muted = r && typeof r != "function" && typeof r != "symbol";
				break;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "defaultValue":
			case "defaultChecked":
			case "innerHTML":
			case "ref": break;
			case "autoFocus": break;
			case "xlinkHref":
				if (r == null || typeof r == "function" || typeof r == "boolean" || typeof r == "symbol") {
					e.removeAttribute("xlink:href");
					break;
				}
				n = rn("" + r), e.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", n);
				break;
			case "contentEditable":
			case "spellCheck":
			case "draggable":
			case "value":
			case "autoReverse":
			case "externalResourcesRequired":
			case "focusable":
			case "preserveAlpha":
				r != null && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, "" + r) : e.removeAttribute(n);
				break;
			case "inert":
			case "allowFullScreen":
			case "async":
			case "autoPlay":
			case "controls":
			case "default":
			case "defer":
			case "disabled":
			case "disablePictureInPicture":
			case "disableRemotePlayback":
			case "formNoValidate":
			case "hidden":
			case "loop":
			case "noModule":
			case "noValidate":
			case "open":
			case "playsInline":
			case "readOnly":
			case "required":
			case "reversed":
			case "scoped":
			case "seamless":
			case "itemScope":
				r && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, "") : e.removeAttribute(n);
				break;
			case "capture":
			case "download":
				!0 === r ? e.setAttribute(n, "") : !1 !== r && r != null && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, r) : e.removeAttribute(n);
				break;
			case "cols":
			case "rows":
			case "size":
			case "span":
				r != null && typeof r != "function" && typeof r != "symbol" && !isNaN(r) && 1 <= r ? e.setAttribute(n, r) : e.removeAttribute(n);
				break;
			case "rowSpan":
			case "start":
				r == null || typeof r == "function" || typeof r == "symbol" || isNaN(r) ? e.removeAttribute(n) : e.setAttribute(n, r);
				break;
			case "popover":
				Q("beforetoggle", e), Q("toggle", e), Nt(e, "popover", r);
				break;
			case "xlinkActuate":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:actuate", r);
				break;
			case "xlinkArcrole":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:arcrole", r);
				break;
			case "xlinkRole":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:role", r);
				break;
			case "xlinkShow":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:show", r);
				break;
			case "xlinkTitle":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:title", r);
				break;
			case "xlinkType":
				Ft(e, "http://www.w3.org/1999/xlink", "xlink:type", r);
				break;
			case "xmlBase":
				Ft(e, "http://www.w3.org/XML/1998/namespace", "xml:base", r);
				break;
			case "xmlLang":
				Ft(e, "http://www.w3.org/XML/1998/namespace", "xml:lang", r);
				break;
			case "xmlSpace":
				Ft(e, "http://www.w3.org/XML/1998/namespace", "xml:space", r);
				break;
			case "is":
				Nt(e, "is", r);
				break;
			case "innerText":
			case "textContent": break;
			default: (!(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (n = tn.get(n) || n, Nt(e, n, r));
		}
	}
	function Nd(e, t, n, r, a, o) {
		switch (n) {
			case "style":
				$t(e, r, o);
				break;
			case "dangerouslySetInnerHTML":
				if (r != null) {
					if (typeof r != "object" || !("__html" in r)) throw Error(i(61));
					if (n = r.__html, n != null) {
						if (a.children != null) throw Error(i(60));
						e.innerHTML = n;
					}
				}
				break;
			case "children":
				typeof r == "string" ? Xt(e, r) : (typeof r == "number" || typeof r == "bigint") && Xt(e, "" + r);
				break;
			case "onScroll":
				r != null && Q("scroll", e);
				break;
			case "onScrollEnd":
				r != null && Q("scrollend", e);
				break;
			case "onClick":
				r != null && (e.onclick = an);
				break;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "innerHTML":
			case "ref": break;
			case "innerText":
			case "textContent": break;
			default: if (!Et.hasOwnProperty(n)) a: {
				if (n[0] === "o" && n[1] === "n" && (a = n.endsWith("Capture"), t = n.slice(2, a ? n.length - 7 : void 0), o = e[ft] || null, o = o == null ? null : o[n], typeof o == "function" && e.removeEventListener(t, o, a), typeof r == "function")) {
					typeof o != "function" && o !== null && (n in e ? e[n] = null : e.hasAttribute(n) && e.removeAttribute(n)), e.addEventListener(t, r, a);
					break a;
				}
				n in e ? e[n] = r : !0 === r ? e.setAttribute(n, "") : Nt(e, n, r);
			}
		}
	}
	function Pd(e, t, n) {
		switch (t) {
			case "div":
			case "span":
			case "svg":
			case "path":
			case "a":
			case "g":
			case "p":
			case "li": break;
			case "img":
				Q("error", e), Q("load", e);
				var r = !1, a = !1, o;
				for (o in n) if (n.hasOwnProperty(o)) {
					var s = n[o];
					if (s != null) switch (o) {
						case "src":
							r = !0;
							break;
						case "srcSet":
							a = !0;
							break;
						case "children":
						case "dangerouslySetInnerHTML": throw Error(i(137, t));
						default: $(e, t, o, s, n, null);
					}
				}
				a && $(e, t, "srcSet", n.srcSet, n, null), r && $(e, t, "src", n.src, n, null);
				return;
			case "input":
				Q("invalid", e);
				var c = o = s = a = null, l = null, u = null;
				for (r in n) if (n.hasOwnProperty(r)) {
					var d = n[r];
					if (d != null) switch (r) {
						case "name":
							a = d;
							break;
						case "type":
							s = d;
							break;
						case "checked":
							l = d;
							break;
						case "defaultChecked":
							u = d;
							break;
						case "value":
							o = d;
							break;
						case "defaultValue":
							c = d;
							break;
						case "children":
						case "dangerouslySetInnerHTML":
							if (d != null) throw Error(i(137, t));
							break;
						default: $(e, t, r, d, n, null);
					}
				}
				Gt(e, o, c, l, u, s, a, !1);
				return;
			case "select":
				for (a in Q("invalid", e), r = s = o = null, n) if (n.hasOwnProperty(a) && (c = n[a], c != null)) switch (a) {
					case "value":
						o = c;
						break;
					case "defaultValue":
						s = c;
						break;
					case "multiple": r = c;
					default: $(e, t, a, c, n, null);
				}
				t = o, n = s, e.multiple = !!r, t == null ? n != null && qt(e, !!r, n, !0) : qt(e, !!r, t, !1);
				return;
			case "textarea":
				for (s in Q("invalid", e), o = a = r = null, n) if (n.hasOwnProperty(s) && (c = n[s], c != null)) switch (s) {
					case "value":
						r = c;
						break;
					case "defaultValue":
						a = c;
						break;
					case "children":
						o = c;
						break;
					case "dangerouslySetInnerHTML":
						if (c != null) throw Error(i(91));
						break;
					default: $(e, t, s, c, n, null);
				}
				Yt(e, r, a, o);
				return;
			case "option":
				for (l in n) if (n.hasOwnProperty(l) && (r = n[l], r != null)) switch (l) {
					case "selected":
						e.selected = r && typeof r != "function" && typeof r != "symbol";
						break;
					default: $(e, t, l, r, n, null);
				}
				return;
			case "dialog":
				Q("beforetoggle", e), Q("toggle", e), Q("cancel", e), Q("close", e);
				break;
			case "iframe":
			case "object":
				Q("load", e);
				break;
			case "video":
			case "audio":
				for (r = 0; r < _d.length; r++) Q(_d[r], e);
				break;
			case "image":
				Q("error", e), Q("load", e);
				break;
			case "details":
				Q("toggle", e);
				break;
			case "embed":
			case "source":
			case "link": Q("error", e), Q("load", e);
			case "area":
			case "base":
			case "br":
			case "col":
			case "hr":
			case "keygen":
			case "meta":
			case "param":
			case "track":
			case "wbr":
			case "menuitem":
				for (u in n) if (n.hasOwnProperty(u) && (r = n[u], r != null)) switch (u) {
					case "children":
					case "dangerouslySetInnerHTML": throw Error(i(137, t));
					default: $(e, t, u, r, n, null);
				}
				return;
			default: if (en(t)) {
				for (d in n) n.hasOwnProperty(d) && (r = n[d], r !== void 0 && Nd(e, t, d, r, n, void 0));
				return;
			}
		}
		for (c in n) n.hasOwnProperty(c) && (r = n[c], r != null && $(e, t, c, r, n, null));
	}
	function Fd(e, t, n, r) {
		switch (t) {
			case "div":
			case "span":
			case "svg":
			case "path":
			case "a":
			case "g":
			case "p":
			case "li": break;
			case "input":
				var a = null, o = null, s = null, c = null, l = null, u = null, d = null;
				for (m in n) {
					var f = n[m];
					if (n.hasOwnProperty(m) && f != null) switch (m) {
						case "checked": break;
						case "value": break;
						case "defaultValue": l = f;
						default: r.hasOwnProperty(m) || $(e, t, m, null, r, f);
					}
				}
				for (var p in r) {
					var m = r[p];
					if (f = n[p], r.hasOwnProperty(p) && (m != null || f != null)) switch (p) {
						case "type":
							o = m;
							break;
						case "name":
							a = m;
							break;
						case "checked":
							u = m;
							break;
						case "defaultChecked":
							d = m;
							break;
						case "value":
							s = m;
							break;
						case "defaultValue":
							c = m;
							break;
						case "children":
						case "dangerouslySetInnerHTML":
							if (m != null) throw Error(i(137, t));
							break;
						default: m !== f && $(e, t, p, m, r, f);
					}
				}
				Wt(e, s, c, l, u, d, o, a);
				return;
			case "select":
				for (o in m = s = c = p = null, n) if (l = n[o], n.hasOwnProperty(o) && l != null) switch (o) {
					case "value": break;
					case "multiple": m = l;
					default: r.hasOwnProperty(o) || $(e, t, o, null, r, l);
				}
				for (a in r) if (o = r[a], l = n[a], r.hasOwnProperty(a) && (o != null || l != null)) switch (a) {
					case "value":
						p = o;
						break;
					case "defaultValue":
						c = o;
						break;
					case "multiple": s = o;
					default: o !== l && $(e, t, a, o, r, l);
				}
				t = c, n = s, r = m, p == null ? !!r != !!n && (t == null ? qt(e, !!n, n ? [] : "", !1) : qt(e, !!n, t, !0)) : qt(e, !!n, p, !1);
				return;
			case "textarea":
				for (c in m = p = null, n) if (a = n[c], n.hasOwnProperty(c) && a != null && !r.hasOwnProperty(c)) switch (c) {
					case "value": break;
					case "children": break;
					default: $(e, t, c, null, r, a);
				}
				for (s in r) if (a = r[s], o = n[s], r.hasOwnProperty(s) && (a != null || o != null)) switch (s) {
					case "value":
						p = a;
						break;
					case "defaultValue":
						m = a;
						break;
					case "children": break;
					case "dangerouslySetInnerHTML":
						if (a != null) throw Error(i(91));
						break;
					default: a !== o && $(e, t, s, a, r, o);
				}
				Jt(e, p, m);
				return;
			case "option":
				for (var h in n) if (p = n[h], n.hasOwnProperty(h) && p != null && !r.hasOwnProperty(h)) switch (h) {
					case "selected":
						e.selected = !1;
						break;
					default: $(e, t, h, null, r, p);
				}
				for (l in r) if (p = r[l], m = n[l], r.hasOwnProperty(l) && p !== m && (p != null || m != null)) switch (l) {
					case "selected":
						e.selected = p && typeof p != "function" && typeof p != "symbol";
						break;
					default: $(e, t, l, p, r, m);
				}
				return;
			case "img":
			case "link":
			case "area":
			case "base":
			case "br":
			case "col":
			case "embed":
			case "hr":
			case "keygen":
			case "meta":
			case "param":
			case "source":
			case "track":
			case "wbr":
			case "menuitem":
				for (var g in n) p = n[g], n.hasOwnProperty(g) && p != null && !r.hasOwnProperty(g) && $(e, t, g, null, r, p);
				for (u in r) if (p = r[u], m = n[u], r.hasOwnProperty(u) && p !== m && (p != null || m != null)) switch (u) {
					case "children":
					case "dangerouslySetInnerHTML":
						if (p != null) throw Error(i(137, t));
						break;
					default: $(e, t, u, p, r, m);
				}
				return;
			default: if (en(t)) {
				for (var _ in n) p = n[_], n.hasOwnProperty(_) && p !== void 0 && !r.hasOwnProperty(_) && Nd(e, t, _, void 0, r, p);
				for (d in r) p = r[d], m = n[d], !r.hasOwnProperty(d) || p === m || p === void 0 && m === void 0 || Nd(e, t, d, p, r, m);
				return;
			}
		}
		for (var v in n) p = n[v], n.hasOwnProperty(v) && p != null && !r.hasOwnProperty(v) && $(e, t, v, null, r, p);
		for (f in r) p = r[f], m = n[f], !r.hasOwnProperty(f) || p === m || p == null && m == null || $(e, t, f, p, r, m);
	}
	function Id(e) {
		switch (e) {
			case "css":
			case "script":
			case "font":
			case "img":
			case "image":
			case "input":
			case "link": return !0;
			default: return !1;
		}
	}
	function Ld() {
		if (typeof performance.getEntriesByType == "function") {
			for (var e = 0, t = 0, n = performance.getEntriesByType("resource"), r = 0; r < n.length; r++) {
				var i = n[r], a = i.transferSize, o = i.initiatorType, s = i.duration;
				if (a && s && Id(o)) {
					for (o = 0, s = i.responseEnd, r += 1; r < n.length; r++) {
						var c = n[r], l = c.startTime;
						if (l > s) break;
						var u = c.transferSize, d = c.initiatorType;
						u && Id(d) && (c = c.responseEnd, o += u * (c < s ? 1 : (s - l) / (c - l)));
					}
					if (--r, t += 8 * (a + o) / (i.duration / 1e3), e++, 10 < e) break;
				}
			}
			if (0 < e) return t / e / 1e6;
		}
		return navigator.connection && (e = navigator.connection.downlink, typeof e == "number") ? e : 5;
	}
	var Rd = null, zd = null;
	function Bd(e) {
		return e.nodeType === 9 ? e : e.ownerDocument;
	}
	function Vd(e) {
		switch (e) {
			case "http://www.w3.org/2000/svg": return 1;
			case "http://www.w3.org/1998/Math/MathML": return 2;
			default: return 0;
		}
	}
	function Hd(e, t) {
		if (e === 0) switch (t) {
			case "svg": return 1;
			case "math": return 2;
			default: return 0;
		}
		return e === 1 && t === "foreignObject" ? 0 : e;
	}
	function Ud(e, t) {
		return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.children == "bigint" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
	}
	var Wd = null;
	function Gd() {
		var e = window.event;
		return e && e.type === "popstate" ? e !== Wd && (Wd = e, !0) : (Wd = null, !1);
	}
	var Kd = typeof setTimeout == "function" ? setTimeout : void 0, qd = typeof clearTimeout == "function" ? clearTimeout : void 0, Jd = typeof Promise == "function" ? Promise : void 0, Yd = typeof queueMicrotask == "function" ? queueMicrotask : Jd === void 0 ? Kd : function(e) {
		return Jd.resolve(null).then(e).catch(Xd);
	};
	function Xd(e) {
		setTimeout(function() {
			throw e;
		});
	}
	function Zd(e) {
		return e === "head";
	}
	function Qd(e, t) {
		var n = t, r = 0;
		do {
			var i = n.nextSibling;
			if (e.removeChild(n), i && i.nodeType === 8) {
				if (n = i.data, n === "/$" || n === "/&") {
					if (r === 0) {
						e.removeChild(i), Np(t);
						return;
					}
					r--;
				} else if (n === "$" || n === "$?" || n === "$~" || n === "$!" || n === "&") r++;
				else if (n === "html") pf(e.ownerDocument.documentElement);
				else if (n === "head") {
					n = e.ownerDocument.head, pf(n);
					for (var a = n.firstChild; a;) {
						var o = a.nextSibling, s = a.nodeName;
						a[vt] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && a.rel.toLowerCase() === "stylesheet" || n.removeChild(a), a = o;
					}
				} else n === "body" && pf(e.ownerDocument.body);
			}
			n = i;
		} while (n);
		Np(t);
	}
	function $d(e, t) {
		var n = e;
		e = 0;
		do {
			var r = n.nextSibling;
			if (n.nodeType === 1 ? t ? (n._stashedDisplay = n.style.display, n.style.display = "none") : (n.style.display = n._stashedDisplay || "", n.getAttribute("style") === "" && n.removeAttribute("style")) : n.nodeType === 3 && (t ? (n._stashedText = n.nodeValue, n.nodeValue = "") : n.nodeValue = n._stashedText || ""), r && r.nodeType === 8) {
				if (n = r.data, n === "/$") {
					if (e === 0) break;
					e--;
				} else n !== "$" && n !== "$?" && n !== "$~" && n !== "$!" || e++;
			}
			n = r;
		} while (n);
	}
	function ef(e) {
		var t = e.firstChild;
		for (t && t.nodeType === 10 && (t = t.nextSibling); t;) {
			var n = t;
			switch (t = t.nextSibling, n.nodeName) {
				case "HTML":
				case "HEAD":
				case "BODY":
					ef(n), yt(n);
					continue;
				case "SCRIPT":
				case "STYLE": continue;
				case "LINK": if (n.rel.toLowerCase() === "stylesheet") continue;
			}
			e.removeChild(n);
		}
	}
	function tf(e, t, n, r) {
		for (; e.nodeType === 1;) {
			var i = n;
			if (e.nodeName.toLowerCase() !== t.toLowerCase()) {
				if (!r && (e.nodeName !== "INPUT" || e.type !== "hidden")) break;
			} else if (!r) {
				if (t === "input" && e.type === "hidden") {
					var a = i.name == null ? null : "" + i.name;
					if (i.type === "hidden" && e.getAttribute("name") === a) return e;
				} else return e;
			} else if (!e[vt]) switch (t) {
				case "meta":
					if (!e.hasAttribute("itemprop")) break;
					return e;
				case "link":
					if (a = e.getAttribute("rel"), a === "stylesheet" && e.hasAttribute("data-precedence") || a !== i.rel || e.getAttribute("href") !== (i.href == null || i.href === "" ? null : i.href) || e.getAttribute("crossorigin") !== (i.crossOrigin == null ? null : i.crossOrigin) || e.getAttribute("title") !== (i.title == null ? null : i.title)) break;
					return e;
				case "style":
					if (e.hasAttribute("data-precedence")) break;
					return e;
				case "script":
					if (a = e.getAttribute("src"), (a !== (i.src == null ? null : i.src) || e.getAttribute("type") !== (i.type == null ? null : i.type) || e.getAttribute("crossorigin") !== (i.crossOrigin == null ? null : i.crossOrigin)) && a && e.hasAttribute("async") && !e.hasAttribute("itemprop")) break;
					return e;
				default: return e;
			}
			if (e = cf(e.nextSibling), e === null) break;
		}
		return null;
	}
	function nf(e, t, n) {
		if (t === "") return null;
		for (; e.nodeType !== 3;) if ((e.nodeType !== 1 || e.nodeName !== "INPUT" || e.type !== "hidden") && !n || (e = cf(e.nextSibling), e === null)) return null;
		return e;
	}
	function rf(e, t) {
		for (; e.nodeType !== 8;) if ((e.nodeType !== 1 || e.nodeName !== "INPUT" || e.type !== "hidden") && !t || (e = cf(e.nextSibling), e === null)) return null;
		return e;
	}
	function af(e) {
		return e.data === "$?" || e.data === "$~";
	}
	function of(e) {
		return e.data === "$!" || e.data === "$?" && e.ownerDocument.readyState !== "loading";
	}
	function sf(e, t) {
		var n = e.ownerDocument;
		if (e.data === "$~") e._reactRetry = t;
		else if (e.data !== "$?" || n.readyState !== "loading") t();
		else {
			var r = function() {
				t(), n.removeEventListener("DOMContentLoaded", r);
			};
			n.addEventListener("DOMContentLoaded", r), e._reactRetry = r;
		}
	}
	function cf(e) {
		for (; e != null; e = e.nextSibling) {
			var t = e.nodeType;
			if (t === 1 || t === 3) break;
			if (t === 8) {
				if (t = e.data, t === "$" || t === "$!" || t === "$?" || t === "$~" || t === "&" || t === "F!" || t === "F") break;
				if (t === "/$" || t === "/&") return null;
			}
		}
		return e;
	}
	var lf = null;
	function uf(e) {
		e = e.nextSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "/$" || n === "/&") {
					if (t === 0) return cf(e.nextSibling);
					t--;
				} else n !== "$" && n !== "$!" && n !== "$?" && n !== "$~" && n !== "&" || t++;
			}
			e = e.nextSibling;
		}
		return null;
	}
	function df(e) {
		e = e.previousSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "$" || n === "$!" || n === "$?" || n === "$~" || n === "&") {
					if (t === 0) return e;
					t--;
				} else n !== "/$" && n !== "/&" || t++;
			}
			e = e.previousSibling;
		}
		return null;
	}
	function ff(e, t, n) {
		switch (t = Bd(n), e) {
			case "html":
				if (e = t.documentElement, !e) throw Error(i(452));
				return e;
			case "head":
				if (e = t.head, !e) throw Error(i(453));
				return e;
			case "body":
				if (e = t.body, !e) throw Error(i(454));
				return e;
			default: throw Error(i(451));
		}
	}
	function pf(e) {
		for (var t = e.attributes; t.length;) e.removeAttributeNode(t[0]);
		yt(e);
	}
	var mf = /* @__PURE__ */ new Map(), hf = /* @__PURE__ */ new Set();
	function gf(e) {
		return typeof e.getRootNode == "function" ? e.getRootNode() : e.nodeType === 9 ? e : e.ownerDocument;
	}
	var _f = M.d;
	M.d = {
		f: vf,
		r: yf,
		D: Sf,
		C: Cf,
		L: wf,
		m: Tf,
		X: Df,
		S: Ef,
		M: Of
	};
	function vf() {
		var e = _f.f(), t = bu();
		return e || t;
	}
	function yf(e) {
		var t = xt(e);
		t !== null && t.tag === 5 && t.type === "form" ? Cs(t) : _f.r(e);
	}
	var bf = typeof document > "u" ? null : document;
	function xf(e, t, n) {
		var r = bf;
		if (r && typeof t == "string" && t) {
			var i = Ut(t);
			i = "link[rel=\"" + e + "\"][href=\"" + i + "\"]", typeof n == "string" && (i += "[crossorigin=\"" + n + "\"]"), hf.has(i) || (hf.add(i), e = {
				rel: e,
				crossOrigin: n,
				href: t
			}, r.querySelector(i) === null && (t = r.createElement("link"), Pd(t, "link", e), wt(t), r.head.appendChild(t)));
		}
	}
	function Sf(e) {
		_f.D(e), xf("dns-prefetch", e, null);
	}
	function Cf(e, t) {
		_f.C(e, t), xf("preconnect", e, t);
	}
	function wf(e, t, n) {
		_f.L(e, t, n);
		var r = bf;
		if (r && e && t) {
			var i = "link[rel=\"preload\"][as=\"" + Ut(t) + "\"]";
			t === "image" && n && n.imageSrcSet ? (i += "[imagesrcset=\"" + Ut(n.imageSrcSet) + "\"]", typeof n.imageSizes == "string" && (i += "[imagesizes=\"" + Ut(n.imageSizes) + "\"]")) : i += "[href=\"" + Ut(e) + "\"]";
			var a = i;
			switch (t) {
				case "style":
					a = Af(e);
					break;
				case "script": a = Pf(e);
			}
			mf.has(a) || (e = h({
				rel: "preload",
				href: t === "image" && n && n.imageSrcSet ? void 0 : e,
				as: t
			}, n), mf.set(a, e), r.querySelector(i) !== null || t === "style" && r.querySelector(jf(a)) || t === "script" && r.querySelector(Ff(a)) || (t = r.createElement("link"), Pd(t, "link", e), wt(t), r.head.appendChild(t)));
		}
	}
	function Tf(e, t) {
		_f.m(e, t);
		var n = bf;
		if (n && e) {
			var r = t && typeof t.as == "string" ? t.as : "script", i = "link[rel=\"modulepreload\"][as=\"" + Ut(r) + "\"][href=\"" + Ut(e) + "\"]", a = i;
			switch (r) {
				case "audioworklet":
				case "paintworklet":
				case "serviceworker":
				case "sharedworker":
				case "worker":
				case "script": a = Pf(e);
			}
			if (!mf.has(a) && (e = h({
				rel: "modulepreload",
				href: e
			}, t), mf.set(a, e), n.querySelector(i) === null)) {
				switch (r) {
					case "audioworklet":
					case "paintworklet":
					case "serviceworker":
					case "sharedworker":
					case "worker":
					case "script": if (n.querySelector(Ff(a))) return;
				}
				r = n.createElement("link"), Pd(r, "link", e), wt(r), n.head.appendChild(r);
			}
		}
	}
	function Ef(e, t, n) {
		_f.S(e, t, n);
		var r = bf;
		if (r && e) {
			var i = Ct(r).hoistableStyles, a = Af(e);
			t = t || "default";
			var o = i.get(a);
			if (!o) {
				var s = {
					loading: 0,
					preload: null
				};
				if (o = r.querySelector(jf(a))) s.loading = 5;
				else {
					e = h({
						rel: "stylesheet",
						href: e,
						"data-precedence": t
					}, n), (n = mf.get(a)) && Rf(e, n);
					var c = o = r.createElement("link");
					wt(c), Pd(c, "link", e), c._p = new Promise(function(e, t) {
						c.onload = e, c.onerror = t;
					}), c.addEventListener("load", function() {
						s.loading |= 1;
					}), c.addEventListener("error", function() {
						s.loading |= 2;
					}), s.loading |= 4, Lf(o, t, r);
				}
				o = {
					type: "stylesheet",
					instance: o,
					count: 1,
					state: s
				}, i.set(a, o);
			}
		}
	}
	function Df(e, t) {
		_f.X(e, t);
		var n = bf;
		if (n && e) {
			var r = Ct(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), wt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function Of(e, t) {
		_f.M(e, t);
		var n = bf;
		if (n && e) {
			var r = Ct(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0,
				type: "module"
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), wt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function kf(e, t, n, r) {
		var a = (a = fe.current) ? gf(a) : null;
		if (!a) throw Error(i(446));
		switch (e) {
			case "meta":
			case "title": return null;
			case "style": return typeof n.precedence == "string" && typeof n.href == "string" ? (t = Af(n.href), n = Ct(a).hoistableStyles, r = n.get(t), r || (r = {
				type: "style",
				instance: null,
				count: 0,
				state: null
			}, n.set(t, r)), r) : {
				type: "void",
				instance: null,
				count: 0,
				state: null
			};
			case "link":
				if (n.rel === "stylesheet" && typeof n.href == "string" && typeof n.precedence == "string") {
					e = Af(n.href);
					var o = Ct(a).hoistableStyles, s = o.get(e);
					if (s || (a = a.ownerDocument || a, s = {
						type: "stylesheet",
						instance: null,
						count: 0,
						state: {
							loading: 0,
							preload: null
						}
					}, o.set(e, s), (o = a.querySelector(jf(e))) && !o._p && (s.instance = o, s.state.loading = 5), mf.has(e) || (n = {
						rel: "preload",
						as: "style",
						href: n.href,
						crossOrigin: n.crossOrigin,
						integrity: n.integrity,
						media: n.media,
						hrefLang: n.hrefLang,
						referrerPolicy: n.referrerPolicy
					}, mf.set(e, n), o || Nf(a, e, n, s.state))), t && r === null) throw Error(i(528, ""));
					return s;
				}
				if (t && r !== null) throw Error(i(529, ""));
				return null;
			case "script": return t = n.async, n = n.src, typeof n == "string" && t && typeof t != "function" && typeof t != "symbol" ? (t = Pf(n), n = Ct(a).hoistableScripts, r = n.get(t), r || (r = {
				type: "script",
				instance: null,
				count: 0,
				state: null
			}, n.set(t, r)), r) : {
				type: "void",
				instance: null,
				count: 0,
				state: null
			};
			default: throw Error(i(444, e));
		}
	}
	function Af(e) {
		return "href=\"" + Ut(e) + "\"";
	}
	function jf(e) {
		return "link[rel=\"stylesheet\"][" + e + "]";
	}
	function Mf(e) {
		return h({}, e, {
			"data-precedence": e.precedence,
			precedence: null
		});
	}
	function Nf(e, t, n, r) {
		e.querySelector("link[rel=\"preload\"][as=\"style\"][" + t + "]") ? r.loading = 1 : (t = e.createElement("link"), r.preload = t, t.addEventListener("load", function() {
			return r.loading |= 1;
		}), t.addEventListener("error", function() {
			return r.loading |= 2;
		}), Pd(t, "link", n), wt(t), e.head.appendChild(t));
	}
	function Pf(e) {
		return "[src=\"" + Ut(e) + "\"]";
	}
	function Ff(e) {
		return "script[async]" + e;
	}
	function If(e, t, n) {
		if (t.count++, t.instance === null) switch (t.type) {
			case "style":
				var r = e.querySelector("style[data-href~=\"" + Ut(n.href) + "\"]");
				if (r) return t.instance = r, wt(r), r;
				var a = h({}, n, {
					"data-href": n.href,
					"data-precedence": n.precedence,
					href: null,
					precedence: null
				});
				return r = (e.ownerDocument || e).createElement("style"), wt(r), Pd(r, "style", a), Lf(r, n.precedence, e), t.instance = r;
			case "stylesheet":
				a = Af(n.href);
				var o = e.querySelector(jf(a));
				if (o) return t.state.loading |= 4, t.instance = o, wt(o), o;
				r = Mf(n), (a = mf.get(a)) && Rf(r, a), o = (e.ownerDocument || e).createElement("link"), wt(o);
				var s = o;
				return s._p = new Promise(function(e, t) {
					s.onload = e, s.onerror = t;
				}), Pd(o, "link", r), t.state.loading |= 4, Lf(o, n.precedence, e), t.instance = o;
			case "script": return o = Pf(n.src), (a = e.querySelector(Ff(o))) ? (t.instance = a, wt(a), a) : (r = n, (a = mf.get(o)) && (r = h({}, n), zf(r, a)), e = e.ownerDocument || e, a = e.createElement("script"), wt(a), Pd(a, "link", r), e.head.appendChild(a), t.instance = a);
			case "void": return null;
			default: throw Error(i(443, t.type));
		}
		else t.type === "stylesheet" && !(t.state.loading & 4) && (r = t.instance, t.state.loading |= 4, Lf(r, n.precedence, e));
		return t.instance;
	}
	function Lf(e, t, n) {
		for (var r = n.querySelectorAll("link[rel=\"stylesheet\"][data-precedence],style[data-precedence]"), i = r.length ? r[r.length - 1] : null, a = i, o = 0; o < r.length; o++) {
			var s = r[o];
			if (s.dataset.precedence === t) a = s;
			else if (a !== i) break;
		}
		a ? a.parentNode.insertBefore(e, a.nextSibling) : (t = n.nodeType === 9 ? n.head : n, t.insertBefore(e, t.firstChild));
	}
	function Rf(e, t) {
		e.crossOrigin ?? (e.crossOrigin = t.crossOrigin), e.referrerPolicy ?? (e.referrerPolicy = t.referrerPolicy), e.title ?? (e.title = t.title);
	}
	function zf(e, t) {
		e.crossOrigin ?? (e.crossOrigin = t.crossOrigin), e.referrerPolicy ?? (e.referrerPolicy = t.referrerPolicy), e.integrity ?? (e.integrity = t.integrity);
	}
	var Bf = null;
	function Vf(e, t, n) {
		if (Bf === null) {
			var r = /* @__PURE__ */ new Map(), i = Bf = /* @__PURE__ */ new Map();
			i.set(n, r);
		} else i = Bf, r = i.get(n), r || (r = /* @__PURE__ */ new Map(), i.set(n, r));
		if (r.has(e)) return r;
		for (r.set(e, null), n = n.getElementsByTagName(e), i = 0; i < n.length; i++) {
			var a = n[i];
			if (!(a[vt] || a[dt] || e === "link" && a.getAttribute("rel") === "stylesheet") && a.namespaceURI !== "http://www.w3.org/2000/svg") {
				var o = a.getAttribute(t) || "";
				o = e + o;
				var s = r.get(o);
				s ? s.push(a) : r.set(o, [a]);
			}
		}
		return r;
	}
	function Hf(e, t, n) {
		e = e.ownerDocument || e, e.head.insertBefore(n, t === "title" ? e.querySelector("head > title") : null);
	}
	function Uf(e, t, n) {
		if (n === 1 || t.itemProp != null) return !1;
		switch (e) {
			case "meta":
			case "title": return !0;
			case "style":
				if (typeof t.precedence != "string" || typeof t.href != "string" || t.href === "") break;
				return !0;
			case "link":
				if (typeof t.rel != "string" || typeof t.href != "string" || t.href === "" || t.onLoad || t.onError) break;
				switch (t.rel) {
					case "stylesheet": return e = t.disabled, typeof t.precedence == "string" && e == null;
					default: return !0;
				}
			case "script": if (t.async && typeof t.async != "function" && typeof t.async != "symbol" && !t.onLoad && !t.onError && t.src && typeof t.src == "string") return !0;
		}
		return !1;
	}
	function Wf(e) {
		return !(e.type === "stylesheet" && !(e.state.loading & 3));
	}
	function Gf(e, t, n, r) {
		if (n.type === "stylesheet" && (typeof r.media != "string" || !1 !== matchMedia(r.media).matches) && !(n.state.loading & 4)) {
			if (n.instance === null) {
				var i = Af(r.href), a = t.querySelector(jf(i));
				if (a) {
					t = a._p, typeof t == "object" && t && typeof t.then == "function" && (e.count++, e = Jf.bind(e), t.then(e, e)), n.state.loading |= 4, n.instance = a, wt(a);
					return;
				}
				a = t.ownerDocument || t, r = Mf(r), (i = mf.get(i)) && Rf(r, i), a = a.createElement("link"), wt(a);
				var o = a;
				o._p = new Promise(function(e, t) {
					o.onload = e, o.onerror = t;
				}), Pd(a, "link", r), n.instance = a;
			}
			e.stylesheets === null && (e.stylesheets = /* @__PURE__ */ new Map()), e.stylesheets.set(n, t), (t = n.state.preload) && !(n.state.loading & 3) && (e.count++, n = Jf.bind(e), t.addEventListener("load", n), t.addEventListener("error", n));
		}
	}
	var Kf = 0;
	function qf(e, t) {
		return e.stylesheets && e.count === 0 && Xf(e, e.stylesheets), 0 < e.count || 0 < e.imgCount ? function(n) {
			var r = setTimeout(function() {
				if (e.stylesheets && Xf(e, e.stylesheets), e.unsuspend) {
					var t = e.unsuspend;
					e.unsuspend = null, t();
				}
			}, 6e4 + t);
			0 < e.imgBytes && Kf === 0 && (Kf = 62500 * Ld());
			var i = setTimeout(function() {
				if (e.waitingForImages = !1, e.count === 0 && (e.stylesheets && Xf(e, e.stylesheets), e.unsuspend)) {
					var t = e.unsuspend;
					e.unsuspend = null, t();
				}
			}, (e.imgBytes > Kf ? 50 : 800) + t);
			return e.unsuspend = n, function() {
				e.unsuspend = null, clearTimeout(r), clearTimeout(i);
			};
		} : null;
	}
	function Jf() {
		if (this.count--, this.count === 0 && (this.imgCount === 0 || !this.waitingForImages)) {
			if (this.stylesheets) Xf(this, this.stylesheets);
			else if (this.unsuspend) {
				var e = this.unsuspend;
				this.unsuspend = null, e();
			}
		}
	}
	var Yf = null;
	function Xf(e, t) {
		e.stylesheets = null, e.unsuspend !== null && (e.count++, Yf = /* @__PURE__ */ new Map(), t.forEach(Zf, e), Yf = null, Jf.call(e));
	}
	function Zf(e, t) {
		if (!(t.state.loading & 4)) {
			var n = Yf.get(e);
			if (n) var r = n.get(null);
			else {
				n = /* @__PURE__ */ new Map(), Yf.set(e, n);
				for (var i = e.querySelectorAll("link[data-precedence],style[data-precedence]"), a = 0; a < i.length; a++) {
					var o = i[a];
					(o.nodeName === "LINK" || o.getAttribute("media") !== "not all") && (n.set(o.dataset.precedence, o), r = o);
				}
				r && n.set(null, r);
			}
			i = t.instance, o = i.getAttribute("data-precedence"), a = n.get(o) || r, a === r && n.set(null, i), n.set(o, i), this.count++, r = Jf.bind(this), i.addEventListener("load", r), i.addEventListener("error", r), a ? a.parentNode.insertBefore(i, a.nextSibling) : (e = e.nodeType === 9 ? e.head : e, e.insertBefore(i, e.firstChild)), t.state.loading |= 4;
		}
	}
	var Qf = {
		$$typeof: C,
		Provider: null,
		Consumer: null,
		_currentValue: ae,
		_currentValue2: ae,
		_threadCount: 0
	};
	function $f(e, t, n, r, i, a, o, s, c) {
		this.tag = 1, this.containerInfo = e, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = et(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = et(0), this.hiddenUpdates = et(null), this.identifierPrefix = r, this.onUncaughtError = i, this.onCaughtError = a, this.onRecoverableError = o, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = c, this.incompleteTransitions = /* @__PURE__ */ new Map();
	}
	function ep(e, t, n, r, i, a, o, s, c, l, u, d) {
		return e = new $f(e, t, n, o, c, l, u, d, s), t = 1, !0 === a && (t |= 24), a = ui(3, null, null, t), e.current = a, a.stateNode = e, t = B(), t.refCount++, e.pooledCache = t, t.refCount++, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: t
		}, Ia(a), e;
	}
	function tp(e) {
		return e ? (e = ci, e) : ci;
	}
	function np(e, t, n, r, i, a) {
		i = tp(i), r.context === null ? r.context = i : r.pendingContext = i, r = Ra(t), r.payload = { element: n }, a = a === void 0 ? null : a, a !== null && (r.callback = a), n = za(e, r, t), n !== null && (hu(n, e, t), Ba(n, e, t));
	}
	function rp(e, t) {
		if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
			var n = e.retryLane;
			e.retryLane = n !== 0 && n < t ? n : t;
		}
	}
	function ip(e, t) {
		rp(e, t), (e = e.alternate) && rp(e, t);
	}
	function ap(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = ai(e, 67108864);
			t !== null && hu(t, e, 67108864), ip(e, 67108864);
		}
	}
	function op(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = pu();
			t = ot(t);
			var n = ai(e, t);
			n !== null && hu(n, e, t), ip(e, t);
		}
	}
	var sp = !0;
	function cp(e, t, n, r) {
		var i = j.T;
		j.T = null;
		var a = M.p;
		try {
			M.p = 2, up(e, t, n, r);
		} finally {
			M.p = a, j.T = i;
		}
	}
	function lp(e, t, n, r) {
		var i = j.T;
		j.T = null;
		var a = M.p;
		try {
			M.p = 8, up(e, t, n, r);
		} finally {
			M.p = a, j.T = i;
		}
	}
	function up(e, t, n, r) {
		if (sp) {
			var i = dp(r);
			if (i === null) wd(e, t, r, fp, n), Cp(e, r);
			else if (Tp(i, e, t, n, r)) r.stopPropagation();
			else if (Cp(e, r), t & 4 && -1 < Sp.indexOf(e)) {
				for (; i !== null;) {
					var a = xt(i);
					if (a !== null) switch (a.tag) {
						case 3:
							if (a = a.stateNode, a.current.memoizedState.isDehydrated) {
								var o = Ye(a.pendingLanes);
								if (o !== 0) {
									var s = a;
									for (s.pendingLanes |= 2, s.entangledLanes |= 2; o;) {
										var c = 1 << 31 - He(o);
										s.entanglements[1] |= c, o &= ~c;
									}
									rd(a), !(q & 6) && (tu = Ae() + 500, id(0, !1));
								}
							}
							break;
						case 31:
						case 13: s = ai(a, 2), s !== null && hu(s, a, 2), bu(), ip(a, 2);
					}
					if (a = dp(r), a === null && wd(e, t, r, fp, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else wd(e, t, r, null, n);
		}
	}
	function dp(e) {
		return e = sn(e), pp(e);
	}
	var fp = null;
	function pp(e) {
		if (fp = null, e = bt(e), e !== null) {
			var t = o(e);
			if (t === null) e = null;
			else {
				var n = t.tag;
				if (n === 13) {
					if (e = s(t), e !== null) return e;
					e = null;
				} else if (n === 31) {
					if (e = c(t), e !== null) return e;
					e = null;
				} else if (n === 3) {
					if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
					e = null;
				} else t !== e && (e = null);
			}
		}
		return fp = e, null;
	}
	function mp(e) {
		switch (e) {
			case "beforetoggle":
			case "cancel":
			case "click":
			case "close":
			case "contextmenu":
			case "copy":
			case "cut":
			case "auxclick":
			case "dblclick":
			case "dragend":
			case "dragstart":
			case "drop":
			case "focusin":
			case "focusout":
			case "input":
			case "invalid":
			case "keydown":
			case "keypress":
			case "keyup":
			case "mousedown":
			case "mouseup":
			case "paste":
			case "pause":
			case "play":
			case "pointercancel":
			case "pointerdown":
			case "pointerup":
			case "ratechange":
			case "reset":
			case "resize":
			case "seeked":
			case "submit":
			case "toggle":
			case "touchcancel":
			case "touchend":
			case "touchstart":
			case "volumechange":
			case "change":
			case "selectionchange":
			case "textInput":
			case "compositionstart":
			case "compositionend":
			case "compositionupdate":
			case "beforeblur":
			case "afterblur":
			case "beforeinput":
			case "blur":
			case "fullscreenchange":
			case "focus":
			case "hashchange":
			case "popstate":
			case "select":
			case "selectstart": return 2;
			case "drag":
			case "dragenter":
			case "dragexit":
			case "dragleave":
			case "dragover":
			case "mousemove":
			case "mouseout":
			case "mouseover":
			case "pointermove":
			case "pointerout":
			case "pointerover":
			case "scroll":
			case "touchmove":
			case "wheel":
			case "mouseenter":
			case "mouseleave":
			case "pointerenter":
			case "pointerleave": return 8;
			case "message": switch (je()) {
				case Me: return 2;
				case Ne: return 8;
				case Pe:
				case Fe: return 32;
				case Ie: return 268435456;
				default: return 32;
			}
			default: return 32;
		}
	}
	var hp = !1, gp = null, _p = null, vp = null, yp = /* @__PURE__ */ new Map(), bp = /* @__PURE__ */ new Map(), xp = [], Sp = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(" ");
	function Cp(e, t) {
		switch (e) {
			case "focusin":
			case "focusout":
				gp = null;
				break;
			case "dragenter":
			case "dragleave":
				_p = null;
				break;
			case "mouseover":
			case "mouseout":
				vp = null;
				break;
			case "pointerover":
			case "pointerout":
				yp.delete(t.pointerId);
				break;
			case "gotpointercapture":
			case "lostpointercapture": bp.delete(t.pointerId);
		}
	}
	function wp(e, t, n, r, i, a) {
		return e === null || e.nativeEvent !== a ? (e = {
			blockedOn: t,
			domEventName: n,
			eventSystemFlags: r,
			nativeEvent: a,
			targetContainers: [i]
		}, t !== null && (t = xt(t), t !== null && ap(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
	}
	function Tp(e, t, n, r, i) {
		switch (t) {
			case "focusin": return gp = wp(gp, e, t, n, r, i), !0;
			case "dragenter": return _p = wp(_p, e, t, n, r, i), !0;
			case "mouseover": return vp = wp(vp, e, t, n, r, i), !0;
			case "pointerover":
				var a = i.pointerId;
				return yp.set(a, wp(yp.get(a) || null, e, t, n, r, i)), !0;
			case "gotpointercapture": return a = i.pointerId, bp.set(a, wp(bp.get(a) || null, e, t, n, r, i)), !0;
		}
		return !1;
	}
	function Ep(e) {
		var t = bt(e.target);
		if (t !== null) {
			var n = o(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = s(n), t !== null) {
						e.blockedOn = t, lt(e.priority, function() {
							op(n);
						});
						return;
					}
				} else if (t === 31) {
					if (t = c(n), t !== null) {
						e.blockedOn = t, lt(e.priority, function() {
							op(n);
						});
						return;
					}
				} else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
					e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
					return;
				}
			}
		}
		e.blockedOn = null;
	}
	function Dp(e) {
		if (e.blockedOn !== null) return !1;
		for (var t = e.targetContainers; 0 < t.length;) {
			var n = dp(e.nativeEvent);
			if (n === null) {
				n = e.nativeEvent;
				var r = new n.constructor(n.type, n);
				on = r, n.target.dispatchEvent(r), on = null;
			} else return t = xt(n), t !== null && ap(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function Op(e, t, n) {
		Dp(e) && n.delete(t);
	}
	function kp() {
		hp = !1, gp !== null && Dp(gp) && (gp = null), _p !== null && Dp(_p) && (_p = null), vp !== null && Dp(vp) && (vp = null), yp.forEach(Op), bp.forEach(Op);
	}
	function Ap(e, n) {
		e.blockedOn === n && (e.blockedOn = null, hp || (hp = !0, t.unstable_scheduleCallback(t.unstable_NormalPriority, kp)));
	}
	var jp = null;
	function Mp(e) {
		jp !== e && (jp = e, t.unstable_scheduleCallback(t.unstable_NormalPriority, function() {
			jp === e && (jp = null);
			for (var t = 0; t < e.length; t += 3) {
				var n = e[t], r = e[t + 1], i = e[t + 2];
				if (typeof r != "function") {
					if (pp(r || n) === null) continue;
					break;
				}
				var a = xt(n);
				a !== null && (e.splice(t, 3), t -= 3, xs(a, {
					pending: !0,
					data: i,
					method: n.method,
					action: r
				}, r, i));
			}
		}));
	}
	function Np(e) {
		function t(t) {
			return Ap(t, e);
		}
		gp !== null && Ap(gp, e), _p !== null && Ap(_p, e), vp !== null && Ap(vp, e), yp.forEach(t), bp.forEach(t);
		for (var n = 0; n < xp.length; n++) {
			var r = xp[n];
			r.blockedOn === e && (r.blockedOn = null);
		}
		for (; 0 < xp.length && (n = xp[0], n.blockedOn === null);) Ep(n), n.blockedOn === null && xp.shift();
		if (n = (e.ownerDocument || e).$$reactFormReplay, n != null) for (r = 0; r < n.length; r += 3) {
			var i = n[r], a = n[r + 1], o = i[ft] || null;
			if (typeof a == "function") o || Mp(n);
			else if (o) {
				var s = null;
				if (a && a.hasAttribute("formAction")) {
					if (i = a, o = a[ft] || null) s = o.formAction;
					else if (pp(i) !== null) continue;
				} else s = o.action;
				typeof s == "function" ? n[r + 1] = s : (n.splice(r, 3), r -= 3), Mp(n);
			}
		}
	}
	function Pp() {
		function e(e) {
			e.canIntercept && e.info === "react-transition" && e.intercept({
				handler: function() {
					return new Promise(function(e) {
						return i = e;
					});
				},
				focusReset: "manual",
				scroll: "manual"
			});
		}
		function t() {
			i !== null && (i(), i = null), r || setTimeout(n, 20);
		}
		function n() {
			if (!r && !navigation.transition) {
				var e = navigation.currentEntry;
				e && e.url != null && navigation.navigate(e.url, {
					state: e.getState(),
					info: "react-transition",
					history: "replace"
				});
			}
		}
		if (typeof navigation == "object") {
			var r = !1, i = null;
			return navigation.addEventListener("navigate", e), navigation.addEventListener("navigatesuccess", t), navigation.addEventListener("navigateerror", t), setTimeout(n, 100), function() {
				r = !0, navigation.removeEventListener("navigate", e), navigation.removeEventListener("navigatesuccess", t), navigation.removeEventListener("navigateerror", t), i !== null && (i(), i = null);
			};
		}
	}
	function Fp(e) {
		this._internalRoot = e;
	}
	Ip.prototype.render = Fp.prototype.render = function(e) {
		var t = this._internalRoot;
		if (t === null) throw Error(i(409));
		var n = t.current;
		np(n, pu(), e, t, null, null);
	}, Ip.prototype.unmount = Fp.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			np(e.current, 2, null, e, null, null), bu(), t[pt] = null;
		}
	};
	function Ip(e) {
		this._internalRoot = e;
	}
	Ip.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = ct();
			e = {
				blockedOn: null,
				target: e,
				priority: t
			};
			for (var n = 0; n < xp.length && t !== 0 && t < xp[n].priority; n++);
			xp.splice(n, 0, e), n === 0 && Ep(e);
		}
	};
	var Lp = n.version;
	if (Lp !== "19.2.8") throw Error(i(527, Lp, "19.2.8"));
	M.findDOMNode = function(e) {
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(i(188)) : (e = Object.keys(e).join(","), Error(i(268, e)));
		return e = d(t), e = e === null ? null : p(e), e = e === null ? null : e.stateNode, e;
	};
	var Rp = {
		bundleType: 0,
		version: "19.2.8",
		rendererPackageName: "react-dom",
		currentDispatcherRef: j,
		reconcilerVersion: "19.2.8"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var zp = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!zp.isDisabled && zp.supportsFiber) try {
			ze = zp.inject(Rp), Be = zp;
		} catch {}
	}
	e.createRoot = function(e, t) {
		if (!a(e)) throw Error(i(299));
		var n = !1, r = "", o = Ws, s = Gs, c = Ks;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (r = t.identifierPrefix), t.onUncaughtError !== void 0 && (o = t.onUncaughtError), t.onCaughtError !== void 0 && (s = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError)), t = ep(e, 1, !1, null, null, n, r, null, o, s, c, Pp), e[pt] = t.current, Sd(e), new Fp(t);
	};
})), g = /* @__PURE__ */ o(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = h();
})), _ = /* @__PURE__ */ c(u(), 1), v = g(), y = null, b = /* @__PURE__ */ new Set();
function x(e) {
	if (!e || typeof e != "object") return;
	let t = y;
	if (y = e, t !== e) for (let e of Array.from(b)) try {
		e();
	} catch {}
}
function S() {
	return y;
}
function C(e) {
	return b.add(e), () => {
		b.delete(e);
	};
}
function w() {
	return y?.unknownLabel ?? "—";
}
//#endregion
//#region src/lib/dispatcher.ts
var T = /* @__PURE__ */ new Set([
	"shipment_update",
	"navigate",
	"shipment_field_save",
	"delivery_confirm",
	"finance_actual_save",
	"payment_record",
	"payment_correction",
	"shipment_create",
	"pxk_generate",
	"customer_create",
	"customer_edit",
	"customer_archive",
	"customer_import",
	"quote_create",
	"quote_edit",
	"quote_transition",
	"agreement_create",
	"agreement_edit",
	"agreement_transition",
	"contract_create",
	"contract_save",
	"contract_goods_save",
	"contract_docgen_generate",
	"contract_docgen_issue",
	"contract_shipment_link"
]), E = null, D = 0;
function O(e) {
	E = e;
}
function k(e, t) {
	return !E || !T.has(e) ? !1 : (D += 1, E(e, {
		seq: D,
		event: e,
		payload: t
	}), !0);
}
//#endregion
//#region node_modules/react-router/dist/development/chunk-BV7QT456.mjs
var ee = /^(?:[a-z][a-z0-9+.-]*:|[\\/]{2})/i, te = /^[\\/]{2}/;
function ne(e, t) {
	return t + e.replace(/\\/g, "/");
}
function re(e) {
	return typeof e == "object" && !!e && "pathname" in e && "search" in e && "hash" in e && "state" in e && "key" in e;
}
function ie(e = {}) {
	let { initialEntries: t = ["/"], initialIndex: n, v5Compat: r = !1 } = e, i;
	i = t.map((e, t) => u(e, typeof e == "string" ? null : e.state, t === 0 ? "default" : void 0, typeof e == "string" ? void 0 : e.mask));
	let a = c(n ?? i.length - 1), o = "POP", s = null;
	function c(e) {
		return Math.min(Math.max(e, 0), i.length - 1);
	}
	function l() {
		return i[a];
	}
	function u(e, t = null, n, r) {
		let a = ae(i ? l().pathname : "/", e, t, n, r);
		return j(a.pathname.charAt(0) === "/", `relative pathnames are not supported in memory history: ${JSON.stringify(e)}`), a;
	}
	function d(e) {
		return typeof e == "string" ? e : oe(e);
	}
	return {
		get index() {
			return a;
		},
		get action() {
			return o;
		},
		get location() {
			return l();
		},
		createHref: d,
		createURL(e) {
			return new URL(d(e), "http://localhost");
		},
		encodeLocation(e) {
			let t = typeof e == "string" ? se(e) : e;
			return {
				pathname: t.pathname || "",
				search: t.search || "",
				hash: t.hash || ""
			};
		},
		push(e, t) {
			o = "PUSH";
			let n = re(e) ? e : u(e, t);
			a += 1, i.splice(a, i.length, n), r && s && s({
				action: o,
				location: n,
				delta: 1
			});
		},
		replace(e, t) {
			o = "REPLACE";
			let n = re(e) ? e : u(e, t);
			i[a] = n, r && s && s({
				action: o,
				location: n,
				delta: 0
			});
		},
		go(e) {
			o = "POP";
			let t = c(a + e), n = i[t];
			a = t, s && s({
				action: o,
				location: n,
				delta: e
			});
		},
		listen(e) {
			return s = e, () => {
				s = null;
			};
		}
	};
}
function A(e, t) {
	if (e === !1 || e == null) throw Error(t);
}
function j(e, t) {
	if (!e) {
		typeof console < "u" && console.warn(t);
		try {
			throw Error(t);
		} catch {}
	}
}
function M() {
	return Math.random().toString(36).substring(2, 10);
}
function ae(e, t, n = null, r, i) {
	return {
		pathname: typeof e == "string" ? e : e.pathname,
		search: "",
		hash: "",
		...typeof t == "string" ? se(t) : t,
		state: n,
		key: t && t.key || r || M(),
		mask: i
	};
}
function oe({ pathname: e = "/", search: t = "", hash: n = "" }) {
	return t && t !== "?" && (e += t.charAt(0) === "?" ? t : "?" + t), n && n !== "#" && (e += n.charAt(0) === "#" ? n : "#" + n), e;
}
function se(e) {
	let t = {};
	if (e) {
		let n = e.indexOf("#");
		n >= 0 && (t.hash = e.substring(n), e = e.substring(0, n));
		let r = e.indexOf("?");
		r >= 0 && (t.search = e.substring(r), e = e.substring(0, r)), e && (t.pathname = e);
	}
	return t;
}
function ce(e, t, n = "/") {
	return le(e, t, n, !1);
}
function le(e, t, n, r, i) {
	let a = De((typeof t == "string" ? se(t) : t).pathname || "/", n);
	if (a == null) return null;
	let o = i ?? N(e), s = null, c = Ee(a);
	for (let e = 0; s == null && e < o.length; ++e) s = Se(o[e], c, r);
	return s;
}
function N(e) {
	let t = ue(e);
	return fe(t), t;
}
function ue(e, t = [], n = [], r = "", i = !1) {
	let a = (e, a, o = i, s) => {
		let c = {
			relativePath: s === void 0 ? e.path || "" : s,
			caseSensitive: e.caseSensitive === !0,
			childrenIndex: a,
			route: e
		};
		if (c.relativePath.startsWith("/")) {
			if (!c.relativePath.startsWith(r) && o) return;
			A(c.relativePath.startsWith(r), `Absolute route path "${c.relativePath}" nested under path "${r}" is not valid. An absolute child route path must start with the combined path of all its parent routes.`), c.relativePath = c.relativePath.slice(r.length);
		}
		let l = Fe([r, c.relativePath]), u = n.concat(c);
		e.children && e.children.length > 0 && (A(e.index !== !0, `Index routes must not have child routes. Please remove all child routes from route path "${l}".`), ue(e.children, t, u, l, o)), (e.path != null || e.index) && t.push({
			path: l,
			score: be(l, e.index),
			routesMeta: u.map((e, t) => {
				let [n, r] = Te(e.relativePath, e.caseSensitive, t === u.length - 1);
				return {
					...e,
					matcher: n,
					compiledParams: r
				};
			})
		});
	};
	return e.forEach((e, t) => {
		if (e.path === "" || !e.path?.includes("?")) a(e, t);
		else for (let n of de(e.path)) a(e, t, !0, n);
	}), t;
}
function de(e) {
	let t = e.split("/");
	if (t.length === 0) return [];
	let [n, ...r] = t, i = n.endsWith("?"), a = n.replace(/\?$/, "");
	if (r.length === 0) return i ? [a, ""] : [a];
	let o = de(r.join("/")), s = [];
	return s.push(...o.map((e) => e === "" ? a : [a, e].join("/"))), i && s.push(...o), s.map((t) => e.startsWith("/") && t === "" ? "/" : t);
}
function fe(e) {
	e.sort((e, t) => e.score === t.score ? xe(e.routesMeta.map((e) => e.childrenIndex), t.routesMeta.map((e) => e.childrenIndex)) : t.score - e.score);
}
var pe = /^:[\w-]+$/, me = 3, he = 2, ge = 1, _e = 10, ve = -2, ye = (e) => e === "*";
function be(e, t) {
	let n = e.split("/"), r = n.length;
	return n.some(ye) && (r += ve), t && (r += he), n.filter((e) => !ye(e)).reduce((e, t) => e + (pe.test(t) ? me : t === "" ? ge : _e), r);
}
function xe(e, t) {
	return e.length === t.length && e.slice(0, -1).every((e, n) => e === t[n]) ? e[e.length - 1] - t[t.length - 1] : 0;
}
function Se(e, t, n = !1) {
	let { routesMeta: r } = e, i = {}, a = "/", o = [];
	for (let e = 0; e < r.length; ++e) {
		let s = r[e], c = e === r.length - 1, l = a === "/" ? t : t.slice(a.length) || "/", u = {
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: c
		}, d = s.matcher && s.compiledParams ? we(u, l, s.matcher, s.compiledParams) : Ce(u, l), f = s.route;
		if (!d && c && n && !r[r.length - 1].route.index && (d = Ce({
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: !1
		}, l)), !d) return null;
		Object.assign(i, d.params), o.push({
			params: i,
			pathname: Fe([a, d.pathname]),
			pathnameBase: Le(Fe([a, d.pathnameBase])),
			route: f
		}), d.pathnameBase !== "/" && (a = Fe([a, d.pathnameBase]));
	}
	return o;
}
function Ce(e, t) {
	typeof e == "string" && (e = {
		path: e,
		caseSensitive: !1,
		end: !0
	});
	let [n, r] = Te(e.path, e.caseSensitive, e.end);
	return we(e, t, n, r);
}
function we(e, t, n, r) {
	let i = t.match(n);
	if (!i) return null;
	let a = i[0], o = Ie(a, 1), s = i.slice(1);
	return {
		params: r.reduce((e, { paramName: t, isOptional: n }, r) => {
			if (t === "*") {
				let e = s[r] || "";
				o = Ie(a.slice(0, a.length - e.length), 1);
			}
			let i = s[r];
			return e[t] = n && !i ? void 0 : (i || "").replace(/%2F/g, "/"), e;
		}, {}),
		pathname: a,
		pathnameBase: o,
		pattern: e
	};
}
function Te(e, t = !1, n = !0) {
	j(e === "*" || !e.endsWith("*") || e.endsWith("/*"), `Route path "${e}" will be treated as if it were "${e.replace(/\*$/, "/*")}" because the \`*\` character must always follow a \`/\` in the pattern. To get rid of this warning, please change the route path to "${e.replace(/\*$/, "/*")}".`);
	let r = [], i = "^" + e.replace(/\/*\*?$/, "").replace(/^\/*/, "/").replace(/[\\.*+^${}|()[\]]/g, "\\$&").replace(/\/:([\w-]+)(\?)?/g, (e, t, n, i, a) => {
		if (r.push({
			paramName: t,
			isOptional: n != null
		}), n) {
			let t = a.charAt(i + e.length);
			return t && t !== "/" ? "/([^\\/]*)" : "(?:/([^\\/]*))?";
		}
		return "/([^\\/]+)";
	}).replace(/\/([\w-]+)\?(\/|$)/g, "(/$1)?$2");
	return e.endsWith("*") ? (r.push({ paramName: "*" }), i += e === "*" || e === "/*" ? "(.*)$" : "(?:\\/(.+)|\\/*)$") : n ? i += "\\/*$" : e !== "" && e !== "/" && (i += "(?:(?=\\/|$))"), [new RegExp(i, t ? void 0 : "i"), r];
}
function Ee(e) {
	try {
		return e.split("/").map((e) => decodeURIComponent(e).replace(/\//g, "%2F")).join("/");
	} catch (t) {
		return j(!1, `The URL path "${e}" could not be decoded because it is a malformed URL segment. This is probably due to a bad percent encoding (${t}).`), e;
	}
}
function De(e, t) {
	if (t === "/") return e;
	if (!e.toLowerCase().startsWith(t.toLowerCase())) return null;
	let n = t.endsWith("/") ? t.length - 1 : t.length, r = e.charAt(n);
	return r && r !== "/" ? null : e.slice(n) || "/";
}
function Oe(e, t = "/") {
	let { pathname: n, search: r = "", hash: i = "" } = typeof e == "string" ? se(e) : e, a;
	return n ? (n = Pe(n), a = n.startsWith("/") || n.startsWith("\\") ? ke(n.substring(1), "/") : ke(n, t)) : a = t, {
		pathname: a,
		search: Re(r),
		hash: ze(i)
	};
}
function ke(e, t) {
	let n = Ie(t).split("/");
	return e.split("/").forEach((e) => {
		e === ".." ? n.length > 1 && n.pop() : e !== "." && n.push(e);
	}), n.length > 1 ? n.join("/") : "/";
}
function Ae(e, t, n, r) {
	return `Cannot include a '${e}' character in a manually specified \`to.${t}\` field [${JSON.stringify(r)}].  Please separate it out to the \`to.${n}\` field. Alternatively you may provide the full path as a string in <Link to="..."> and the router will parse it for you.`;
}
function je(e) {
	return e.filter((e, t) => t === 0 || e.route.path && e.route.path.length > 0);
}
function Me(e) {
	let t = je(e);
	return t.map((e, n) => n === t.length - 1 ? e.pathname : e.pathnameBase);
}
function Ne(e, t, n, r = !1) {
	let i;
	typeof e == "string" ? i = se(e) : (i = { ...e }, A(!i.pathname || !i.pathname.includes("?"), Ae("?", "pathname", "search", i)), A(!i.pathname || !i.pathname.includes("#"), Ae("#", "pathname", "hash", i)), A(!i.search || !i.search.includes("#"), Ae("#", "search", "hash", i)));
	let a = e === "" || i.pathname === "", o = a ? "/" : i.pathname, s;
	if (o == null) s = n;
	else {
		let e = t.length - 1;
		if (!r && o.startsWith("..")) {
			let t = o.split("/");
			for (; t[0] === "..";) t.shift(), --e;
			i.pathname = t.join("/");
		}
		s = e >= 0 ? t[e] : "/";
	}
	let c = Oe(i, s), l = o && o !== "/" && o.endsWith("/"), u = (a || o === ".") && n.endsWith("/");
	return !c.pathname.endsWith("/") && (l || u) && (c.pathname += "/"), c;
}
var Pe = (e) => e.replace(/[\\/]{2,}/g, "/"), Fe = (e) => Pe(e.join("/"));
function Ie(e, t = 0) {
	let n = e.length;
	for (; n > t && e.charCodeAt(n - 1) === 47;) n--;
	return n === e.length ? e : e.slice(0, n);
}
var Le = (e) => Ie(e).replace(/^\/*/, "/"), Re = (e) => !e || e === "?" ? "" : e.startsWith("?") ? e : "?" + e, ze = (e) => !e || e === "#" ? "" : e.startsWith("#") ? e : "#" + e, Be = class {
	constructor(e, t, n, r = !1) {
		this.status = e, this.statusText = t || "", this.internal = r, n instanceof Error ? (this.data = n.toString(), this.error = n) : this.data = n;
	}
};
function Ve(e) {
	return e != null && typeof e.status == "number" && typeof e.statusText == "string" && typeof e.internal == "boolean" && "data" in e;
}
function He(e) {
	return Fe(e.map((e) => e.route.path).filter(Boolean)) || "/";
}
var Ue = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
function We(e, t) {
	let n = e;
	if (typeof n != "string" || !ee.test(n)) return {
		absoluteURL: void 0,
		isExternal: !1,
		to: n
	};
	let r = n, i = !1;
	if (Ue) try {
		let e = new URL(window.location.href), r = te.test(n) ? new URL(ne(n, e.protocol)) : new URL(n), a = De(r.pathname, t);
		r.origin === e.origin && a != null ? n = a + r.search + r.hash : i = !0;
	} catch {
		j(!1, `<Link to="${n}"> contains an invalid URL which will probably break when clicked - please update to a valid URL path.`);
	}
	return {
		absoluteURL: r,
		isExternal: i,
		to: n
	};
}
Object.getOwnPropertyNames(Object.prototype).sort().join("\0");
var Ge = new URL("http://localhost");
function Ke(e) {
	if (e.createURL) return e.createURL("/");
	try {
		return new URL(e.createHref("/"), Ge);
	} catch {
		return Ge;
	}
}
function qe(e, t) {
	return e.origin === t.origin && (e.origin !== "null" || e.protocol === t.protocol && e.host === t.host);
}
function Je(e, t) {
	if (e.startsWith("//")) return !0;
	let n = t.protocol.toLowerCase();
	return e.toLowerCase().startsWith(n) ? t.host === "" || e.slice(n.length).startsWith("//") : !1;
}
function Ye(e, t, n, r) {
	let i = null;
	try {
		i = e == null ? null : new URL(e, n);
	} catch {}
	let a = new URL(t, n), o = i != null && !qe(i, n), s = !qe(a, n);
	if (r === "reject") {
		if (o || s) throw Error("External navigation is not allowed");
	} else if (s && (i == null || !Je(e, i) || !qe(i, a))) throw Error("External navigation is not allowed");
}
var Xe = [
	"POST",
	"PUT",
	"PATCH",
	"DELETE"
];
new Set(Xe);
var Ze = ["GET", ...Xe];
new Set(Ze);
var Qe = [
	"about:",
	"blob:",
	"chrome:",
	"chrome-untrusted:",
	"content:",
	"data:",
	"devtools:",
	"file:",
	"filesystem:",
	"javascript:"
];
function $e(e) {
	try {
		return Qe.includes(new URL(e).protocol);
	} catch {
		return !1;
	}
}
var et = _.createContext(null);
et.displayName = "DataRouter";
var tt = _.createContext(null);
tt.displayName = "DataRouterState";
var nt = _.createContext(!1);
function rt() {
	return _.useContext(nt);
}
var it = _.createContext({ isTransitioning: !1 });
it.displayName = "ViewTransition";
var at = _.createContext(/* @__PURE__ */ new Map());
at.displayName = "Fetchers";
var ot = _.createContext(null);
ot.displayName = "Await";
var st = _.createContext(null);
st.displayName = "Navigation";
var ct = _.createContext(null);
ct.displayName = "Location";
var lt = _.createContext({
	outlet: null,
	matches: [],
	isDataRoute: !1
});
lt.displayName = "Route";
var ut = _.createContext(null);
ut.displayName = "RouteError";
var dt = "REACT_ROUTER_ERROR", ft = "REDIRECT", pt = "ROUTE_ERROR_RESPONSE";
function mt(e) {
	if (e.startsWith(`${dt}:${ft}:{`)) try {
		let t = JSON.parse(e.slice(28));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string" && typeof t.location == "string" && typeof t.reloadDocument == "boolean" && typeof t.replace == "boolean") return t;
	} catch {}
}
function ht(e) {
	if (e.startsWith(`${dt}:${pt}:{`)) try {
		let t = JSON.parse(e.slice(40));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string") return new Be(t.status, t.statusText, t.data);
	} catch {}
}
function gt(e, { relative: t } = {}) {
	A(_t(), "useHref() may be used only in the context of a <Router> component.");
	let { basename: n, navigator: r } = _.useContext(st), { hash: i, pathname: a, search: o } = wt(e, { relative: t }), s = a;
	return n !== "/" && (s = a === "/" ? n : Fe([n, a])), r.createHref({
		pathname: s,
		search: o,
		hash: i
	});
}
function _t() {
	return _.useContext(ct) != null;
}
function vt() {
	return A(_t(), "useLocation() may be used only in the context of a <Router> component."), _.useContext(ct).location;
}
var yt = "You should call navigate() in a React.useEffect(), not when your component is first rendered.";
function bt(e) {
	_.useContext(st).static || _.useLayoutEffect(e);
}
function xt() {
	let { isDataRoute: e } = _.useContext(lt);
	return e ? Vt() : St();
}
function St() {
	A(_t(), "useNavigate() may be used only in the context of a <Router> component.");
	let e = _.useContext(et), { basename: t, navigator: n } = _.useContext(st), { matches: r } = _.useContext(lt), { pathname: i } = vt(), a = JSON.stringify(Me(r)), o = _.useRef(!1);
	return bt(() => {
		o.current = !0;
	}), _.useCallback((r, s = {}) => {
		if (j(o.current, yt), !o.current) return;
		if (typeof r == "number") {
			n.go(r);
			return;
		}
		let c = Ne(r, JSON.parse(a), i, s.relative === "path");
		e == null && t !== "/" && (c.pathname = c.pathname === "/" ? t : Fe([t, c.pathname])), Ye(typeof r == "string" ? r : oe(r), n.createHref(c), Ke(n), "reject"), (s.replace ? n.replace : n.push)(c, s.state, s);
	}, [
		t,
		n,
		a,
		i,
		e
	]);
}
_.createContext(null);
function Ct() {
	let { matches: e } = _.useContext(lt);
	return e[e.length - 1]?.params ?? {};
}
function wt(e, { relative: t } = {}) {
	let { matches: n } = _.useContext(lt), { pathname: r } = vt(), i = JSON.stringify(Me(n));
	return _.useMemo(() => Ne(e, JSON.parse(i), r, t === "path"), [
		e,
		i,
		r,
		t
	]);
}
function Tt(e, t) {
	return Et(e, t);
}
function Et(e, t, n) {
	A(_t(), "useRoutes() may be used only in the context of a <Router> component.");
	let { navigator: r } = _.useContext(st), { matches: i } = _.useContext(lt), a = i[i.length - 1], o = a ? a.params : {}, s = a ? a.pathname : "/", c = a ? a.pathnameBase : "/", l = a && a.route;
	{
		let e = l && l.path || "";
		Ut(s, !l || e.endsWith("*") || e.endsWith("*?"), `You rendered descendant <Routes> (or called \`useRoutes()\`) at "${s}" (under <Route path="${e}">) but the parent route path has no trailing "*". This means if you navigate deeper, the parent won't match anymore and therefore the child routes will never render.

Please change the parent <Route path="${e}"> to <Route path="${e === "/" ? "*" : `${e}/*`}">.`);
	}
	let u = vt(), d;
	if (t) {
		let e = typeof t == "string" ? se(t) : t;
		A(c === "/" || e.pathname?.startsWith(c), `When overriding the location using \`<Routes location>\` or \`useRoutes(routes, location)\`, the location pathname must begin with the portion of the URL pathname that was matched by all parent routes. The current pathname base is "${c}" but pathname "${e.pathname}" was given in the \`location\` prop.`), d = e;
	} else d = u;
	let f = d.pathname || "/", p = f;
	if (c !== "/") {
		let e = c.replace(/^\//, "").split("/");
		p = "/" + f.replace(/^\//, "").split("/").slice(e.length).join("/");
	}
	let m = n && n.state.matches.length ? n.state.matches.map((e) => Object.assign(e, { route: n.manifest[e.route.id] || e.route })) : ce(e, { pathname: p });
	j(l || m != null, `No routes matched location "${d.pathname}${d.search}${d.hash}" `), j(m == null || m[m.length - 1].route.element !== void 0 || m[m.length - 1].route.Component !== void 0 || m[m.length - 1].route.lazy !== void 0, `Matched leaf route at location "${d.pathname}${d.search}${d.hash}" does not have an element or Component. This means it will render an <Outlet /> with a null value by default resulting in an "empty" page.`);
	let h = Nt(m && m.map((e) => Object.assign({}, e, {
		params: Object.assign({}, o, e.params),
		pathname: Fe([c, r.encodeLocation ? r.encodeLocation(e.pathname.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathname]),
		pathnameBase: e.pathnameBase === "/" ? c : Fe([c, r.encodeLocation ? r.encodeLocation(e.pathnameBase.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathnameBase])
	})), i, n);
	return t && h ? /* @__PURE__ */ _.createElement(ct.Provider, { value: {
		location: {
			pathname: "/",
			search: "",
			hash: "",
			state: null,
			key: "default",
			mask: void 0,
			...d
		},
		navigationType: "POP"
	} }, h) : h;
}
function Dt() {
	let e = Bt(), t = Ve(e) ? `${e.status} ${e.statusText}` : e instanceof Error ? e.message : JSON.stringify(e), n = e instanceof Error ? e.stack : null, r = "rgba(200,200,200, 0.5)", i = {
		padding: "0.5rem",
		backgroundColor: r
	}, a = {
		padding: "2px 4px",
		backgroundColor: r
	}, o = null;
	return console.error("Error handled by React Router default ErrorBoundary:", e), o = /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("p", null, "💿 Hey developer 👋"), /* @__PURE__ */ _.createElement("p", null, "You can provide a way better UX than this when your app throws errors by providing your own ", /* @__PURE__ */ _.createElement("code", { style: a }, "ErrorBoundary"), " or", " ", /* @__PURE__ */ _.createElement("code", { style: a }, "errorElement"), " prop on your route.")), /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("h2", null, "Unexpected Application Error!"), /* @__PURE__ */ _.createElement("h3", { style: { fontStyle: "italic" } }, t), n ? /* @__PURE__ */ _.createElement("pre", { style: i }, n) : null, o);
}
var Ot = /* @__PURE__ */ _.createElement(Dt, null), kt = class extends _.Component {
	constructor(e) {
		super(e), this.state = {
			location: e.location,
			revalidation: e.revalidation,
			error: e.error
		};
	}
	static getDerivedStateFromError(e) {
		return { error: e };
	}
	static getDerivedStateFromProps(e, t) {
		return t.location !== e.location || t.revalidation !== "idle" && e.revalidation === "idle" ? {
			error: e.error,
			location: e.location,
			revalidation: e.revalidation
		} : {
			error: e.error === void 0 ? t.error : e.error,
			location: t.location,
			revalidation: e.revalidation || t.revalidation
		};
	}
	componentDidCatch(e, t) {
		this.props.onError ? this.props.onError(e, t) : console.error("React Router caught the following error during render", e);
	}
	render() {
		let e = this.state.error;
		if (this.context && typeof e == "object" && e && "digest" in e && typeof e.digest == "string") {
			let t = ht(e.digest);
			t && (e = t);
		}
		let t = e === void 0 ? this.props.children : /* @__PURE__ */ _.createElement(lt.Provider, { value: this.props.routeContext }, /* @__PURE__ */ _.createElement(ut.Provider, {
			value: e,
			children: this.props.component
		}));
		return this.context ? /* @__PURE__ */ _.createElement(jt, { error: e }, t) : t;
	}
};
kt.contextType = nt;
var At = /* @__PURE__ */ new WeakMap();
function jt({ children: e, error: t }) {
	let { basename: n, navigator: r } = _.useContext(st);
	if (typeof t == "object" && t && "digest" in t && typeof t.digest == "string") {
		let e = mt(t.digest);
		if (e) {
			let i = At.get(t);
			if (i) throw i;
			let a = We(e.location, n), o = a.absoluteURL || a.to;
			if (Ye(e.location, o, Ke(r), "allow-explicit"), $e(o)) throw Error("Invalid redirect location");
			if (Ue && !At.get(t)) {
				if (a.isExternal || e.reloadDocument) window.location.href = o;
				else {
					let n = Promise.resolve().then(() => window.__reactRouterDataRouter.navigate(a.to, { replace: e.replace }));
					throw At.set(t, n), n;
				}
			}
			return /* @__PURE__ */ _.createElement("meta", {
				httpEquiv: "refresh",
				content: `0;url=${o}`
			});
		}
	}
	return e;
}
function Mt({ routeContext: e, match: t, children: n }) {
	let r = _.useContext(et);
	return r && r.static && r.staticContext && (t.route.errorElement || t.route.ErrorBoundary) && (r.staticContext._deepestRenderedBoundaryId = t.route.id), /* @__PURE__ */ _.createElement(lt.Provider, { value: e }, n);
}
function Nt(e, t = [], n) {
	let r = n?.state;
	if (e == null) {
		if (!r) return null;
		if (r.errors) e = r.matches;
		else if (t.length === 0 && !r.initialized && r.matches.length > 0) e = r.matches;
		else return null;
	}
	let i = e, a = r?.errors;
	if (a != null) {
		let e = i.findIndex((e) => e.route.id && a?.[e.route.id] !== void 0);
		A(e >= 0, `Could not find a matching route for errors on route IDs: ${Object.keys(a).join(",")}`), i = i.slice(0, Math.min(i.length, e + 1));
	}
	let o = !1, s = -1;
	if (n && r) {
		o = r.renderFallback;
		for (let e = 0; e < i.length; e++) {
			let t = i[e];
			if ((t.route.HydrateFallback || t.route.hydrateFallbackElement) && (s = e), t.route.id) {
				let { loaderData: e, errors: a } = r, c = t.route.loader && !e.hasOwnProperty(t.route.id) && (!a || a[t.route.id] === void 0);
				if (t.route.lazy || c) {
					n.isStatic && (o = !0), i = s >= 0 ? i.slice(0, s + 1) : [i[0]];
					break;
				}
			}
		}
	}
	let c = n?.onError, l = r && c ? (e, t) => {
		c(e, {
			location: r.location,
			params: r.matches?.[0]?.params ?? {},
			pattern: He(r.matches),
			errorInfo: t
		});
	} : void 0;
	return i.reduceRight((e, n, c) => {
		let u, d = !1, f = null, p = null;
		r && (u = a && n.route.id ? a[n.route.id] : void 0, f = n.route.errorElement || Ot, o && (s < 0 && c === 0 ? (Ut("route-fallback", !1, "No `HydrateFallback` element provided to render during initial hydration"), d = !0, p = null) : s === c && (d = !0, p = n.route.hydrateFallbackElement || null)));
		let m = t.concat(i.slice(0, c + 1)), h = () => {
			let t;
			return t = u ? f : d ? p : n.route.Component ? /* @__PURE__ */ _.createElement(n.route.Component, null) : n.route.element ? n.route.element : e, /* @__PURE__ */ _.createElement(Mt, {
				match: n,
				routeContext: {
					outlet: e,
					matches: m,
					isDataRoute: r != null
				},
				children: t
			});
		};
		return r && (n.route.ErrorBoundary || n.route.errorElement || c === 0) ? /* @__PURE__ */ _.createElement(kt, {
			location: r.location,
			revalidation: r.revalidation,
			component: f,
			error: u,
			children: h(),
			routeContext: {
				outlet: null,
				matches: m,
				isDataRoute: !0
			},
			onError: l
		}) : h();
	}, null);
}
function Pt(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function Ft(e) {
	let t = _.useContext(et);
	return A(t, Pt(e)), t;
}
function It(e) {
	let t = _.useContext(tt);
	return A(t, Pt(e)), t;
}
function Lt(e) {
	let t = _.useContext(lt);
	return A(t, Pt(e)), t;
}
function Rt(e) {
	let t = Lt(e), n = t.matches[t.matches.length - 1];
	return A(n.route.id, `${e} can only be used on routes that contain a unique "id"`), n.route.id;
}
function zt() {
	return Rt("useRouteId");
}
function Bt() {
	let e = _.useContext(ut), t = It("useRouteError"), n = Rt("useRouteError");
	return e === void 0 ? t.errors?.[n] : e;
}
function Vt() {
	let { router: e } = Ft("useNavigate"), t = Rt("useNavigate"), n = _.useRef(!1);
	return bt(() => {
		n.current = !0;
	}), _.useCallback(async (r, i = {}) => {
		j(n.current, yt), n.current && (typeof r == "number" ? await e.navigate(r) : await e.navigate(r, {
			fromRouteId: t,
			...i
		}));
	}, [e, t]);
}
var Ht = {};
function Ut(e, t, n) {
	!t && !Ht[e] && (Ht[e] = !0, j(!1, n));
}
_.memo(Wt);
function Wt({ routes: e, manifest: t, future: n, state: r, isStatic: i, onError: a }) {
	return Et(e, void 0, {
		manifest: t,
		state: r,
		isStatic: i,
		onError: a,
		future: n
	});
}
function Gt({ basename: e, children: t, initialEntries: n, initialIndex: r, useTransitions: i }) {
	let a = _.useRef();
	a.current ?? (a.current = ie({
		initialEntries: n,
		initialIndex: r,
		v5Compat: !0
	}));
	let o = a.current, [s, c] = _.useState({
		action: o.action,
		location: o.location
	}), l = _.useCallback((e) => {
		i === !1 ? c(e) : _.startTransition(() => c(e));
	}, [i]);
	return _.useLayoutEffect(() => o.listen(l), [o, l]), /* @__PURE__ */ _.createElement(qt, {
		basename: e,
		children: t,
		location: s.location,
		navigationType: s.action,
		navigator: o,
		useTransitions: i
	});
}
function Kt(e) {
	A(!1, "A <Route> is only ever to be used as the child of <Routes> element, never rendered directly. Please wrap your <Route> in a <Routes>.");
}
function qt({ basename: e = "/", children: t = null, location: n, navigationType: r = "POP", navigator: i, static: a = !1, useTransitions: o }) {
	A(!_t(), "You cannot render a <Router> inside another <Router>. You should never have more than one in your app.");
	let s = e.replace(/^\/*/, "/"), c = _.useMemo(() => ({
		basename: s,
		navigator: i,
		static: a,
		useTransitions: o,
		future: {}
	}), [
		s,
		i,
		a,
		o
	]);
	typeof n == "string" && (n = se(n));
	let { pathname: l = "/", search: u = "", hash: d = "", state: f = null, key: p = "default", mask: m } = n, h = _.useMemo(() => {
		let e = De(l, s);
		return e == null ? null : {
			location: {
				pathname: e,
				search: u,
				hash: d,
				state: f,
				key: p,
				mask: m
			},
			navigationType: r
		};
	}, [
		s,
		l,
		u,
		d,
		f,
		p,
		r,
		m
	]);
	return j(h != null, `<Router basename="${s}"> is not able to match the URL "${l}${u}${d}" because it does not start with the basename, so the <Router> won't render anything.`), h == null ? null : /* @__PURE__ */ _.createElement(st.Provider, { value: c }, /* @__PURE__ */ _.createElement(ct.Provider, {
		children: t,
		value: h
	}));
}
function Jt({ children: e, location: t }) {
	return Tt(Yt(e), t);
}
_.Component;
function Yt(e, t = []) {
	let n = [];
	return _.Children.forEach(e, (e, r) => {
		if (!_.isValidElement(e)) return;
		let i = [...t, r];
		if (e.type === _.Fragment) {
			n.push.apply(n, Yt(e.props.children, i));
			return;
		}
		A(e.type === Kt, `[${typeof e.type == "string" ? e.type : e.type.name}] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>`), A(!e.props.index || !e.props.children, "An index route cannot have child routes.");
		let a = {
			id: e.props.id || i.join("-"),
			caseSensitive: e.props.caseSensitive,
			element: e.props.element,
			Component: e.props.Component,
			index: e.props.index,
			path: e.props.path,
			middleware: e.props.middleware,
			loader: e.props.loader,
			action: e.props.action,
			hydrateFallbackElement: e.props.hydrateFallbackElement,
			HydrateFallback: e.props.HydrateFallback,
			errorElement: e.props.errorElement,
			ErrorBoundary: e.props.ErrorBoundary,
			hasErrorBoundary: e.props.hasErrorBoundary === !0 || e.props.ErrorBoundary != null || e.props.errorElement != null,
			shouldRevalidate: e.props.shouldRevalidate,
			handle: e.props.handle,
			lazy: e.props.lazy
		};
		e.props.children && (a.children = Yt(e.props.children, i)), n.push(a);
	}), n;
}
var Xt = "get", Zt = "application/x-www-form-urlencoded";
function Qt(e) {
	return typeof HTMLElement < "u" && e instanceof HTMLElement;
}
function $t(e) {
	return Qt(e) && e.tagName.toLowerCase() === "button";
}
function en(e) {
	return Qt(e) && e.tagName.toLowerCase() === "form";
}
function tn(e) {
	return Qt(e) && e.tagName.toLowerCase() === "input";
}
function nn(e) {
	return !!(e.metaKey || e.altKey || e.ctrlKey || e.shiftKey);
}
function rn(e, t) {
	return e.button === 0 && (!t || t === "_self") && !nn(e);
}
function an(e = "") {
	return new URLSearchParams(typeof e == "string" || Array.isArray(e) || e instanceof URLSearchParams ? e : Object.keys(e).reduce((t, n) => {
		let r = e[n];
		return t.concat(Array.isArray(r) ? r.map((e) => [n, e]) : [[n, r]]);
	}, []));
}
function on(e, t) {
	let n = an(e);
	return t && t.forEach((e, r) => {
		n.has(r) || t.getAll(r).forEach((e) => {
			n.append(r, e);
		});
	}), n;
}
var sn = null;
function cn() {
	if (sn === null) try {
		new FormData(document.createElement("form"), 0), sn = !1;
	} catch {
		sn = !0;
	}
	return sn;
}
var ln = /* @__PURE__ */ new Set([
	"application/x-www-form-urlencoded",
	"multipart/form-data",
	"text/plain"
]);
function un(e) {
	return e != null && !ln.has(e) ? (j(!1, `"${e}" is not a valid \`encType\` for \`<Form>\`/\`<fetcher.Form>\` and will default to "${Zt}"`), null) : e;
}
function dn(e, t) {
	let n, r, i, a, o;
	if (en(e)) {
		let o = e.getAttribute("action");
		r = o ? De(o, t) : null, n = e.getAttribute("method") || Xt, i = un(e.getAttribute("enctype")) || Zt, a = new FormData(e);
	} else if ($t(e) || tn(e) && (e.type === "submit" || e.type === "image")) {
		let o = e.form;
		if (o == null) throw Error("Cannot submit a <button> or <input type=\"submit\"> without a <form>");
		let s = e.getAttribute("formaction") || o.getAttribute("action");
		if (r = s ? De(s, t) : null, n = e.getAttribute("formmethod") || o.getAttribute("method") || Xt, i = un(e.getAttribute("formenctype")) || un(o.getAttribute("enctype")) || Zt, a = new FormData(o, e), !cn()) {
			let { name: t, type: n, value: r } = e;
			if (n === "image") {
				let e = t ? `${t}.` : "";
				a.append(`${e}x`, "0"), a.append(`${e}y`, "0");
			} else t && a.append(t, r);
		}
	} else if (Qt(e)) throw Error("Cannot submit element that is not <form>, <button>, or <input type=\"submit|image\">");
	else n = Xt, r = null, i = Zt, o = e;
	return a && i === "text/plain" && (o = a, a = void 0), {
		action: r,
		method: n.toLowerCase(),
		encType: i,
		formData: a,
		body: o
	};
}
Object.getOwnPropertyNames(Object.prototype).sort().join("\0");
function fn(e, t) {
	if (e === !1 || e == null) throw Error(t);
}
function pn(e, t, n, r) {
	let i = typeof e == "string" ? new URL(e, typeof window > "u" ? "server://singlefetch/" : window.location.origin) : e;
	return i.pathname = n ? i.pathname.endsWith("/") ? `${i.pathname}_.${r}` : `${i.pathname}.${r}` : i.pathname === "/" ? `_root.${r}` : t && De(i.pathname, t) === "/" ? `${Ie(t)}/_root.${r}` : `${Ie(i.pathname)}.${r}`, i;
}
async function mn(e, t) {
	if (e.id in t) return t[e.id];
	try {
		let n = await import(
			/* @vite-ignore */
			/* webpackIgnore: true */
			e.module
);
		return t[e.id] = n, n;
	} catch (t) {
		return console.error(`Error loading route module \`${e.module}\`, reloading page...`), console.error(t), window.__reactRouterContext && window.__reactRouterContext.isSpaMode, window.location.reload(), new Promise(() => {});
	}
}
function hn(e) {
	return e != null && typeof e.page == "string";
}
function gn(e) {
	return e == null ? !1 : e.href == null ? e.rel === "preload" && typeof e.imageSrcSet == "string" && typeof e.imageSizes == "string" : typeof e.rel == "string" && typeof e.href == "string";
}
async function _n(e, t, n) {
	return Sn((await Promise.all(e.map(async (e) => {
		let r = t.routes[e.route.id];
		if (r) {
			let e = await mn(r, n);
			return e.links ? e.links() : [];
		}
		return [];
	}))).flat(1).filter(gn).filter((e) => e.rel === "stylesheet" || e.rel === "preload").map((e) => e.rel === "stylesheet" ? {
		...e,
		rel: "prefetch",
		as: "style"
	} : {
		...e,
		rel: "prefetch"
	}));
}
function vn(e, t, n, r, i, a) {
	let o = (e, t) => !n[t] || e.route.id !== n[t].route.id, s = (e, t) => n[t].pathname !== e.pathname || n[t].route.path?.endsWith("*") && n[t].params["*"] !== e.params["*"];
	return a === "assets" ? t.filter((e, t) => o(e, t) || s(e, t)) : a === "data" ? t.filter((t, a) => {
		let c = r.routes[t.route.id];
		if (!c || !c.hasLoader) return !1;
		if (o(t, a) || s(t, a)) return !0;
		if (t.route.shouldRevalidate) {
			let r = t.route.shouldRevalidate({
				currentUrl: new URL(i.pathname + i.search + i.hash, window.origin),
				currentParams: n[0]?.params || {},
				nextUrl: new URL(e, window.origin),
				nextParams: t.params,
				defaultShouldRevalidate: !0
			});
			if (typeof r == "boolean") return r;
		}
		return !0;
	}) : [];
}
function yn(e, t, { includeHydrateFallback: n } = {}) {
	return bn(e.map((e) => {
		let r = t.routes[e.route.id];
		if (!r) return [];
		let i = [r.module];
		return r.clientActionModule && (i = i.concat(r.clientActionModule)), r.clientLoaderModule && (i = i.concat(r.clientLoaderModule)), n && r.hydrateFallbackModule && (i = i.concat(r.hydrateFallbackModule)), r.imports && (i = i.concat(r.imports)), i;
	}).flat(1));
}
function bn(e) {
	return [...new Set(e)];
}
function xn(e) {
	let t = {}, n = Object.keys(e).sort();
	for (let r of n) t[r] = e[r];
	return t;
}
function Sn(e, t) {
	let n = /* @__PURE__ */ new Set(), r = new Set(t);
	return e.reduce((e, i) => {
		if (t && !hn(i) && i.as === "script" && i.href && r.has(i.href)) return e;
		let a = JSON.stringify(xn(i));
		return n.has(a) || (n.add(a), e.push({
			key: a,
			link: i
		})), e;
	}, []);
}
function Cn() {
	let e = _.useContext(et);
	return fn(e, "You must render this element inside a <DataRouterContext.Provider> element"), e;
}
function wn() {
	let e = _.useContext(tt);
	return fn(e, "You must render this element inside a <DataRouterStateContext.Provider> element"), e;
}
var Tn = _.createContext(void 0);
Tn.displayName = "FrameworkContext";
function En() {
	let e = _.useContext(Tn);
	return fn(e, "You must render this element inside a <HydratedRouter> element"), e;
}
function Dn(e, t) {
	let n = _.useContext(Tn), [r, i] = _.useState(!1), [a, o] = _.useState(!1), { onFocus: s, onBlur: c, onMouseEnter: l, onMouseLeave: u, onTouchStart: d } = t, f = _.useRef(null);
	_.useEffect(() => {
		if (e === "render" && o(!0), e === "viewport") {
			let e = new IntersectionObserver((e) => {
				e.forEach((e) => {
					o(e.isIntersecting);
				});
			}, { threshold: .5 });
			return f.current && e.observe(f.current), () => {
				e.disconnect();
			};
		}
	}, [e]), _.useEffect(() => {
		if (r) {
			let e = setTimeout(() => {
				o(!0);
			}, 100);
			return () => {
				clearTimeout(e);
			};
		}
	}, [r]);
	let p = () => {
		i(!0);
	}, m = () => {
		i(!1), o(!1);
	};
	return n ? e === "intent" ? [
		a,
		f,
		{
			onFocus: On(s, p),
			onBlur: On(c, m),
			onMouseEnter: On(l, p),
			onMouseLeave: On(u, m),
			onTouchStart: On(d, p)
		}
	] : [
		a,
		f,
		{}
	] : [
		!1,
		f,
		{}
	];
}
function On(e, t) {
	return (n) => {
		e && e(n), n.defaultPrevented || t(n);
	};
}
function kn({ page: e, ...t }) {
	let n = rt(), { nonce: r } = En(), { router: i } = Cn(), a = _.useMemo(() => ce(i.routes, e, i.basename), [
		i.routes,
		e,
		i.basename
	]);
	return a ? (t.nonce == null && r && (t = {
		...t,
		nonce: r
	}), n ? /* @__PURE__ */ _.createElement(jn, {
		page: e,
		matches: a,
		...t
	}) : /* @__PURE__ */ _.createElement(Mn, {
		page: e,
		matches: a,
		...t
	})) : null;
}
function An(e) {
	let { manifest: t, routeModules: n } = En(), [r, i] = _.useState([]);
	return _.useEffect(() => {
		let r = !1;
		return _n(e, t, n).then((e) => {
			r || i(e);
		}), () => {
			r = !0;
		};
	}, [
		e,
		t,
		n
	]), r;
}
function jn({ page: e, matches: t, ...n }) {
	let r = vt(), { future: i } = En(), { basename: a } = Cn(), o = _.useMemo(() => {
		if (e === r.pathname + r.search + r.hash) return [];
		let n = pn(e, a, i.v8_trailingSlashAwareDataRequests, "rsc"), o = !1, s = [];
		for (let e of t) typeof e.route.shouldRevalidate == "function" ? o = !0 : s.push(e.route.id);
		return o && s.length > 0 && n.searchParams.set("_routes", s.join(",")), [n.pathname + n.search];
	}, [
		a,
		i.v8_trailingSlashAwareDataRequests,
		e,
		r,
		t
	]);
	return /* @__PURE__ */ _.createElement(_.Fragment, null, o.map((e) => /* @__PURE__ */ _.createElement("link", {
		key: e,
		rel: "prefetch",
		as: "fetch",
		href: e,
		...n
	})));
}
function Mn({ page: e, matches: t, ...n }) {
	let r = vt(), { future: i, manifest: a, routeModules: o } = En(), { basename: s } = Cn(), { loaderData: c, matches: l } = wn(), u = _.useMemo(() => vn(e, t, l, a, r, "data"), [
		e,
		t,
		l,
		a,
		r
	]), d = _.useMemo(() => vn(e, t, l, a, r, "assets"), [
		e,
		t,
		l,
		a,
		r
	]), f = _.useMemo(() => {
		if (e === r.pathname + r.search + r.hash) return [];
		let n = /* @__PURE__ */ new Set(), l = !1;
		if (t.forEach((e) => {
			let t = a.routes[e.route.id];
			t && t.hasLoader && (!u.some((t) => t.route.id === e.route.id) && e.route.id in c && o[e.route.id]?.shouldRevalidate || t.hasClientLoader ? l = !0 : n.add(e.route.id));
		}), n.size === 0) return [];
		let d = pn(e, s, i.v8_trailingSlashAwareDataRequests, "data");
		return l && n.size > 0 && d.searchParams.set("_routes", t.filter((e) => n.has(e.route.id)).map((e) => e.route.id).join(",")), [d.pathname + d.search];
	}, [
		s,
		i.v8_trailingSlashAwareDataRequests,
		c,
		r,
		a,
		u,
		t,
		e,
		o
	]), p = _.useMemo(() => yn(d, a), [d, a]), m = An(d);
	return /* @__PURE__ */ _.createElement(_.Fragment, null, f.map((e) => /* @__PURE__ */ _.createElement("link", {
		key: e,
		rel: "prefetch",
		as: "fetch",
		href: e,
		...n
	})), p.map((e) => /* @__PURE__ */ _.createElement("link", {
		key: e,
		rel: "modulepreload",
		href: e,
		...n
	})), m.map(({ key: e, link: t }) => /* @__PURE__ */ _.createElement("link", {
		key: e,
		nonce: n.nonce,
		...t,
		crossOrigin: t.crossOrigin ?? n.crossOrigin
	})));
}
function Nn(...e) {
	return (t) => {
		e.forEach((e) => {
			typeof e == "function" ? e(t) : e != null && (e.current = t);
		});
	};
}
_.Component;
var Pn = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
try {
	Pn && (window.__reactRouterVersion = "7.18.3");
} catch {}
var P = _.forwardRef(function({ onClick: e, discover: t = "render", prefetch: n = "none", relative: r, reloadDocument: i, replace: a, mask: o, state: s, target: c, to: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) {
	let { basename: h, navigator: g, useTransitions: v } = _.useContext(st), y = typeof l == "string" && ee.test(l), b = We(l, h);
	l = b.to;
	let x = gt(l, { relative: r }), S = vt(), C = null;
	if (o) {
		let e = Ne(o, [], S.mask ? S.mask.pathname : "/", !0);
		h !== "/" && (e.pathname = e.pathname === "/" ? h : Fe([h, e.pathname])), C = g.createHref(e);
	}
	let [w, T, E] = Dn(n, p), D = zn(l, {
		replace: a,
		mask: o,
		state: s,
		target: c,
		preventScrollReset: u,
		relative: r,
		viewTransition: d,
		defaultShouldRevalidate: f,
		useTransitions: v
	});
	function O(t) {
		e && e(t), t.defaultPrevented || D(t);
	}
	let k = !(b.isExternal || i), te = /* @__PURE__ */ _.createElement("a", {
		...p,
		...E,
		href: (k ? C : void 0) || b.absoluteURL || x,
		onClick: k ? O : e,
		ref: Nn(m, T),
		target: c,
		"data-discover": !y && t === "render" ? "true" : void 0
	});
	return w && !y ? /* @__PURE__ */ _.createElement(_.Fragment, null, te, /* @__PURE__ */ _.createElement(kn, { page: x })) : te;
});
P.displayName = "Link";
var Fn = _.forwardRef(function({ "aria-current": e = "page", caseSensitive: t = !1, className: n = "", end: r = !1, style: i, to: a, viewTransition: o, children: s, ...c }, l) {
	let u = wt(a, { relative: c.relative }), d = vt(), f = _.useContext(tt), { navigator: p, basename: m } = _.useContext(st), h = f != null && Gn(u) && o === !0, g = p.encodeLocation ? p.encodeLocation(u).pathname : u.pathname, v = d.pathname, y = f && f.navigation && f.navigation.location ? f.navigation.location.pathname : null;
	t || (v = v.toLowerCase(), y = y ? y.toLowerCase() : null, g = g.toLowerCase()), y && m && (y = De(y, m) || y);
	let b = g !== "/" && g.endsWith("/") ? g.length - 1 : g.length, x = v === g || !r && v.startsWith(g) && v.charAt(b) === "/", S = y != null && (y === g || !r && y.startsWith(g) && y.charAt(g.length) === "/"), C = {
		isActive: x,
		isPending: S,
		isTransitioning: h
	}, w = x ? e : void 0, T;
	T = typeof n == "function" ? n(C) : [
		n,
		x ? "active" : null,
		S ? "pending" : null,
		h ? "transitioning" : null
	].filter(Boolean).join(" ");
	let E = typeof i == "function" ? i(C) : i;
	return /* @__PURE__ */ _.createElement(P, {
		...c,
		"aria-current": w,
		className: T,
		ref: l,
		style: E,
		to: a,
		viewTransition: o
	}, typeof s == "function" ? s(C) : s);
});
Fn.displayName = "NavLink";
var In = _.forwardRef(({ discover: e = "render", fetcherKey: t, navigate: n, reloadDocument: r, replace: i, state: a, method: o = Xt, action: s, onSubmit: c, relative: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) => {
	let { useTransitions: h } = _.useContext(st), g = Un(), v = Wn(s, { relative: l }), y = o.toLowerCase() === "get" ? "get" : "post", b = typeof s == "string" && ee.test(s);
	return /* @__PURE__ */ _.createElement("form", {
		ref: m,
		method: y,
		action: v,
		onSubmit: r ? c : (e) => {
			if (c && c(e), e.defaultPrevented) return;
			e.preventDefault();
			let r = e.nativeEvent.submitter, s = r?.getAttribute("formmethod") || o, p = () => g(r || e.currentTarget, {
				fetcherKey: t,
				method: s,
				navigate: n,
				replace: i,
				state: a,
				relative: l,
				preventScrollReset: u,
				viewTransition: d,
				defaultShouldRevalidate: f
			});
			h && n !== !1 ? _.startTransition(() => p()) : p();
		},
		...p,
		"data-discover": !b && e === "render" ? "true" : void 0
	});
});
In.displayName = "Form";
function Ln(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function Rn(e) {
	let t = _.useContext(et);
	return A(t, Ln(e)), t;
}
function zn(e, { target: t, replace: n, mask: r, state: i, preventScrollReset: a, relative: o, viewTransition: s, defaultShouldRevalidate: c, useTransitions: l } = {}) {
	let u = xt(), d = vt(), f = wt(e, { relative: o });
	return _.useCallback((p) => {
		if (rn(p, t)) {
			p.preventDefault();
			let t = n === void 0 ? oe(d) === oe(f) : n, m = () => u(e, {
				replace: t,
				mask: r,
				state: i,
				preventScrollReset: a,
				relative: o,
				viewTransition: s,
				defaultShouldRevalidate: c
			});
			l ? _.startTransition(() => m()) : m();
		}
	}, [
		d,
		u,
		f,
		n,
		r,
		i,
		t,
		e,
		a,
		o,
		s,
		c,
		l
	]);
}
function Bn(e) {
	j(typeof URLSearchParams < "u", "You cannot use the `useSearchParams` hook in a browser that does not support the URLSearchParams API. If you need to support Internet Explorer 11, we recommend you load a polyfill such as https://github.com/ungap/url-search-params.");
	let t = _.useRef(an(e)), n = _.useRef(!1), r = vt(), i = _.useMemo(() => on(r.search, n.current ? null : t.current), [r.search]), a = xt();
	return [i, _.useCallback((e, t) => {
		let r = an(typeof e == "function" ? e(new URLSearchParams(i)) : e);
		n.current = !0, a("?" + r, t);
	}, [a, i])];
}
var Vn = 0, Hn = () => `__${String(++Vn)}__`;
function Un() {
	let { router: e } = Rn("useSubmit"), { basename: t } = _.useContext(st), n = zt(), r = e.fetch, i = e.navigate;
	return _.useCallback(async (e, a = {}) => {
		let { action: o, method: s, encType: c, formData: l, body: u } = dn(e, t);
		if (a.navigate === !1) {
			let e = a.fetcherKey || Hn();
			await r(e, n, a.action || o, {
				defaultShouldRevalidate: a.defaultShouldRevalidate,
				preventScrollReset: a.preventScrollReset,
				formData: l,
				body: u,
				formMethod: a.method || s,
				formEncType: a.encType || c,
				flushSync: a.flushSync
			});
		} else await i(a.action || o, {
			defaultShouldRevalidate: a.defaultShouldRevalidate,
			preventScrollReset: a.preventScrollReset,
			formData: l,
			body: u,
			formMethod: a.method || s,
			formEncType: a.encType || c,
			replace: a.replace,
			state: a.state,
			fromRouteId: n,
			flushSync: a.flushSync,
			viewTransition: a.viewTransition
		});
	}, [
		r,
		i,
		t,
		n
	]);
}
function Wn(e, { relative: t } = {}) {
	let { basename: n } = _.useContext(st), r = _.useContext(lt);
	A(r, "useFormAction must be used inside a RouteContext");
	let [i] = r.matches.slice(-1), a = { ...wt(e || ".", { relative: t }) }, o = vt();
	if (e == null) {
		a.search = o.search;
		let e = new URLSearchParams(a.search), t = e.getAll("index");
		if (t.some((e) => e === "")) {
			e.delete("index"), t.filter((e) => e).forEach((t) => e.append("index", t));
			let n = e.toString();
			a.search = n ? `?${n}` : "";
		}
	}
	return (!e || e === ".") && i.route.index && (a.search = a.search ? a.search.replace(/^\?/, "?index&") : "?index"), n !== "/" && (a.pathname = a.pathname === "/" ? n : Fe([n, a.pathname])), oe(a);
}
function Gn(e, { relative: t } = {}) {
	let n = _.useContext(it);
	A(n != null, "`useViewTransitionState` must be used within `react-router-dom`'s `RouterProvider`.  Did you accidentally import `RouterProvider` from `react-router`?");
	let { basename: r } = Rn("useViewTransitionState"), i = wt(e, { relative: t });
	if (!n.isTransitioning) return !1;
	let a = De(n.currentLocation.pathname, r) || n.currentLocation.pathname, o = De(n.nextLocation.pathname, r) || n.nextLocation.pathname;
	return Ce(i.pathname, o) != null || Ce(i.pathname, a) != null;
}
//#endregion
//#region node_modules/react/cjs/react-jsx-runtime.production.js
var Kn = /* @__PURE__ */ o(((e) => {
	var t = Symbol.for("react.transitional.element"), n = Symbol.for("react.fragment");
	function r(e, n, r) {
		var i = null;
		if (r !== void 0 && (i = "" + r), n.key !== void 0 && (i = "" + n.key), "key" in n) for (var a in r = {}, n) a !== "key" && (r[a] = n[a]);
		else r = n;
		return n = r.ref, {
			$$typeof: t,
			type: e,
			key: i,
			ref: n === void 0 ? null : n,
			props: r
		};
	}
	e.Fragment = n, e.jsx = r, e.jsxs = r;
})), F = (/* @__PURE__ */ o(((e, t) => {
	t.exports = Kn();
})))(), qn = (0, _.createContext)(null), Jn = 0;
function Yn({ children: e }) {
	let t = (0, _.useSyncExternalStore)(C, S, S), [n, r] = (0, _.useState)(t?.user.role ?? "SUPPORT"), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(!1), [f, p] = (0, _.useState)(!1), [m, h] = (0, _.useState)([]), [g, v] = (0, _.useState)({}), y = (0, _.useCallback)((e) => {
		h((t) => t.filter((t) => t.id !== e));
	}, []), b = (0, _.useCallback)((e, t, n = "blue") => {
		Jn += 1;
		let r = Jn;
		h((i) => [...i.slice(-3), {
			id: r,
			title: e,
			desc: t,
			tone: n
		}]), window.setTimeout(() => y(r), 6e3);
	}, [y]), x = (0, _.useMemo)(() => {
		let e = t?.shipments ?? [];
		return Object.keys(g).length === 0 ? e : e.map((e) => g[e.id] ?? e);
	}, [t, g]), T = (0, _.useMemo)(() => t?.contracts ?? [], [t]), E = (0, _.useMemo)(() => t?.tasks ?? [], [t]), D = (0, _.useMemo)(() => t?.customers ?? [], [t]), O = (0, _.useMemo)(() => t?.quotes ?? [], [t]), ee = (0, _.useMemo)(() => t?.agreements ?? [], [t]), te = (0, _.useMemo)(() => t?.authority ?? {
		companies: [],
		agents: []
	}, [t]), ne = (0, _.useMemo)(() => t?.notifications ?? [], [t]), re = (0, _.useMemo)(() => t?.home ?? null, [t]), ie = (0, _.useMemo)(() => t?.environment ?? null, [t]), A = (0, _.useCallback)((e, t) => k(e, t), []), j = (0, _.useCallback)((e, n) => {
		let r = (t?.shipments ?? []).find((t) => t.id === e) ?? Object.values(g).find((t) => t.id === e);
		if (!r) return;
		let i = n(r);
		v((t) => ({
			...t,
			[e]: i
		})), k("shipment_update", { shipment: i });
	}, [t, g]), M = t?.version, ae = (0, _.useRef)(M);
	M !== ae.current && (ae.current = M, t && v((e) => {
		let n = new Set((t.shipments ?? []).map((e) => e.id)), r = {};
		for (let [i, a] of Object.entries(e)) {
			let e = (t.shipments ?? []).find((e) => e.id === i);
			e && JSON.stringify(e) === JSON.stringify(a) || n.has(i) && (r[i] = a);
		}
		return r;
	}));
	let oe = t?.user.name ?? "Thu Hằng", se = (0, _.useMemo)(() => ({
		role: n,
		setRole: r,
		userName: oe,
		query: i,
		setQuery: a,
		searchOpen: o,
		setSearchOpen: s,
		navOpen: c,
		setNavOpen: l,
		notifOpen: u,
		setNotifOpen: d,
		quickAddOpen: f,
		setQuickAddOpen: p,
		toasts: m,
		dismissToast: y,
		toast: b,
		shipments: x,
		contracts: T,
		customers: D,
		quotes: O,
		agreements: ee,
		authority: te,
		tasks: E,
		notifications: ne,
		home: re,
		environment: ie,
		unknownLabel: w(),
		dispatch: A,
		updateShipment: j
	}), [
		n,
		oe,
		i,
		o,
		c,
		u,
		f,
		m,
		y,
		b,
		x,
		T,
		D,
		O,
		ee,
		te,
		E,
		ne,
		re,
		ie,
		A,
		j
	]);
	return /* @__PURE__ */ (0, F.jsx)(qn.Provider, {
		value: se,
		children: e
	});
}
function Xn() {
	let e = (0, _.useContext)(qn);
	if (!e) throw Error("useStore must be used inside <StoreProvider>");
	return e;
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toKebabCase.mjs
var Zn = (e) => e?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toLucideIconData.mjs
function Qn(e, t, n = []) {
	if (t == null) throw Error("[lucide]: iconNode is required when icon name is used");
	return {
		name: Zn(e),
		size: 24,
		node: t,
		...n.length > 0 ? { aliases: n } : {}
	};
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toCamelCase.mjs
var $n = (e) => {
	let t = "", n = !1;
	for (let r of e) {
		if (r === "-" || r === "_" || r <= " ") {
			n = t.length > 0;
			continue;
		}
		t.length === 0 ? t += r.toLowerCase() : t += n ? r.toUpperCase() : r, n = !1;
	}
	return t;
}, er = (e) => {
	let t = $n(e);
	return t.charAt(0).toUpperCase() + t.slice(1);
}, tr = (...e) => e.filter((e, t, n) => !!e && e.trim() !== "" && n.indexOf(e) === t).join(" ").trim(), nr = {
	xmlns: "http://www.w3.org/2000/svg",
	width: 24,
	height: 24,
	viewBox: "0 0 24 24",
	fill: "none",
	stroke: "currentColor",
	"stroke-width": 2,
	"stroke-linecap": "round",
	"stroke-linejoin": "round"
};
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/build/buildLucideIconNode.mjs
function rr(e) {
	return e != null;
}
function ir(e, t = {}) {
	let n = t.attributeNames ?? {}, r = (e) => n[e] ?? e, i = e.size ?? e.width ?? nr.width, a = e.size ?? e.height ?? nr.height, o = e.aliases?.filter((e) => typeof e == "string" && e.trim() !== "").map((e) => `lucide-${e}`) ?? [], s = [...e.name ? [`lucide-${e.name}`] : [], ...o], c = t.className?.split(" ").filter(Boolean) ?? [], l = t.includeDefaultClasses === !1 ? tr(...c) : tr("lucide", ...s, ...c), u = t.absoluteStrokeWidth ? Number(t.strokeWidth ?? nr["stroke-width"]) * Number(e.size ?? e.width ?? nr.width) / Number(t.size ?? t.width ?? nr.width) : t.strokeWidth ?? nr["stroke-width"];
	return [
		"svg",
		{
			...Object.entries(nr).reduce((e, [t, n]) => (e[r(t)] = n, e), {}),
			..."color" in t && t.color && { [r("stroke")]: t.color },
			..."size" in t && rr(t.size) && {
				[r("width")]: t.size,
				[r("height")]: t.size
			},
			..."width" in t && rr(t.width) && { [r("width")]: t.width },
			..."height" in t && rr(t.height) && { [r("height")]: t.height },
			[r("stroke-width")]: u,
			...l && { [r("class")]: l },
			[r("viewBox")]: `0 0 ${i} ${a}`,
			...t.hasA11yProp === !1 ? { [r("aria-hidden")]: "true" } : {},
			..."attributes" in t && t.attributes
		},
		e.node.map((e) => {
			let [n, i, a] = e, o = t.nonScalingStroke ? {
				[r("vector-effect")]: "non-scaling-stroke",
				...i
			} : i;
			return a ? [
				n,
				o,
				a
			] : [n, o];
		})
	];
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/build/buildLucideIconForReact.mjs
function ar(e, t = {}) {
	return ir(e, {
		...t,
		attributeNames: {
			...t.attributeNames,
			class: "className",
			"stroke-width": "strokeWidth",
			"stroke-linecap": "strokeLinecap",
			"stroke-linejoin": "strokeLinejoin",
			"vector-effect": "vectorEffect"
		}
	});
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/hasA11yProp.mjs
var or = (e) => {
	for (let t in e) if (t.startsWith("aria-") || t === "role" || t === "title") return !0;
	return !1;
}, sr = (0, _.createContext)({}), cr = () => (0, _.useContext)(sr), lr = (0, _.forwardRef)(({ color: e, size: t, width: n, height: r, strokeWidth: i, absoluteStrokeWidth: a, nonScalingStroke: o, className: s = "", children: c, iconNode: l = [], icon: u = {
	node: l,
	aliases: [],
	size: 24
}, ...d }, f) => {
	let { size: p = 24, strokeWidth: m = 2, absoluteStrokeWidth: h = !1, nonScalingStroke: g = !1, color: v = "currentColor", className: y = "" } = cr() ?? {}, b = !!c || or(d), [x, S, C = []] = ar(u, {
		color: e ?? v,
		width: n ?? t ?? p,
		height: r ?? t ?? p,
		strokeWidth: i ?? m,
		absoluteStrokeWidth: a ?? h,
		nonScalingStroke: o ?? g,
		className: tr(y, s),
		hasA11yProp: b,
		attributes: d
	});
	return (0, _.createElement)(x, {
		ref: f,
		...S
	}, [...C.map(([e, t]) => (0, _.createElement)(e, t)), ...Array.isArray(c) ? c : [c]]);
});
//#endregion
//#region node_modules/lucide-react/dist/esm/createLucideIcon.mjs
function I(e, t = [], n = []) {
	let r = typeof e == "string" ? Qn(e, t, n) : e, i = (0, _.forwardRef)(({ className: e, ...t }, n) => (0, _.createElement)(lr, {
		ref: n,
		icon: r,
		className: e,
		...t
	}));
	return r.name && (i.displayName = er(r.name)), i;
}
//#endregion
//#region node_modules/lucide-react/dist/esm/icons/archive.mjs
var ur = {
	name: "archive",
	size: 24,
	node: [
		["rect", {
			width: "20",
			height: "5",
			x: "2",
			y: "3",
			rx: "1",
			key: "1wp1u1"
		}],
		["path", {
			d: "M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8",
			key: "1s80jp"
		}],
		["path", {
			d: "M10 12h4",
			key: "a56b0p"
		}]
	]
};
ur.node;
var dr = I(ur), fr = {
	name: "arrow-left",
	size: 24,
	node: [["path", {
		d: "m12 19-7-7 7-7",
		key: "1l729n"
	}], ["path", {
		d: "M19 12H5",
		key: "x3x0zl"
	}]]
};
fr.node;
var pr = I(fr), mr = {
	name: "arrow-right",
	size: 24,
	node: [["path", {
		d: "M5 12h14",
		key: "1ays0h"
	}], ["path", {
		d: "m12 5 7 7-7 7",
		key: "xquz4c"
	}]]
};
mr.node;
var hr = I(mr), gr = {
	name: "banknote",
	size: 24,
	node: [
		["rect", {
			width: "20",
			height: "12",
			x: "2",
			y: "6",
			rx: "2",
			key: "9lu3g6"
		}],
		["circle", {
			cx: "12",
			cy: "12",
			r: "2",
			key: "1c9p78"
		}],
		["path", {
			d: "M6 12h.01M18 12h.01",
			key: "113zkx"
		}]
	]
};
gr.node;
var _r = I(gr), vr = {
	name: "bell-ring",
	size: 24,
	node: [
		["path", {
			d: "M10.268 21a2 2 0 0 0 3.464 0",
			key: "vwvbt9"
		}],
		["path", {
			d: "M22 8c0-2.3-.8-4.3-2-6",
			key: "5bb3ad"
		}],
		["path", {
			d: "M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326",
			key: "11g9vi"
		}],
		["path", {
			d: "M4 2C2.8 3.7 2 5.7 2 8",
			key: "tap9e0"
		}]
	]
};
vr.node;
var yr = I(vr), br = {
	name: "bell",
	size: 24,
	node: [["path", {
		d: "M10.268 21a2 2 0 0 0 3.464 0",
		key: "vwvbt9"
	}], ["path", {
		d: "M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326",
		key: "11g9vi"
	}]]
};
br.node;
var xr = I(br), Sr = {
	name: "book-open",
	size: 24,
	node: [["path", {
		d: "M12 5v16",
		key: "1f6ucr"
	}], ["path", {
		d: "M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z",
		key: "1fyvmf"
	}]]
};
Sr.node;
var Cr = I(Sr), wr = {
	name: "building-2",
	size: 24,
	node: [
		["path", {
			d: "M10 12h4",
			key: "a56b0p"
		}],
		["path", {
			d: "M10 8h4",
			key: "1sr2af"
		}],
		["path", {
			d: "M14 21v-3a2 2 0 0 0-4 0v3",
			key: "1rgiei"
		}],
		["path", {
			d: "M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2",
			key: "secmi2"
		}],
		["path", {
			d: "M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16",
			key: "16ra0t"
		}]
	]
};
wr.node;
var Tr = I(wr), Er = {
	name: "calculator",
	size: 24,
	node: [
		["rect", {
			width: "16",
			height: "20",
			x: "4",
			y: "2",
			rx: "2",
			key: "1nb95v"
		}],
		["line", {
			x1: "8",
			x2: "16",
			y1: "6",
			y2: "6",
			key: "x4nwl0"
		}],
		["line", {
			x1: "16",
			x2: "16",
			y1: "14",
			y2: "18",
			key: "wjye3r"
		}],
		["path", {
			d: "M16 10h.01",
			key: "1m94wz"
		}],
		["path", {
			d: "M12 10h.01",
			key: "1nrarc"
		}],
		["path", {
			d: "M8 10h.01",
			key: "19clt8"
		}],
		["path", {
			d: "M12 14h.01",
			key: "1etili"
		}],
		["path", {
			d: "M8 14h.01",
			key: "6423bh"
		}],
		["path", {
			d: "M12 18h.01",
			key: "mhygvu"
		}],
		["path", {
			d: "M8 18h.01",
			key: "lrp35t"
		}]
	]
};
Er.node;
var Dr = I(Er), Or = {
	name: "chart-column",
	size: 24,
	node: [
		["path", {
			d: "M3 3v16a2 2 0 0 0 2 2h16",
			key: "c24i48"
		}],
		["path", {
			d: "M18 17V9",
			key: "2bz60n"
		}],
		["path", {
			d: "M13 17V5",
			key: "1frdt8"
		}],
		["path", {
			d: "M8 17v-3",
			key: "17ska0"
		}]
	],
	aliases: ["bar-chart-3"]
};
Or.node;
var kr = I(Or), Ar = {
	name: "chevron-right",
	size: 24,
	node: [["path", {
		d: "m9 18 6-6-6-6",
		key: "mthhwq"
	}]]
};
Ar.node;
var jr = I(Ar), Mr = {
	name: "circle-alert",
	size: 24,
	node: [
		["circle", {
			cx: "12",
			cy: "12",
			r: "10",
			key: "1mglay"
		}],
		["line", {
			x1: "12",
			x2: "12",
			y1: "8",
			y2: "12",
			key: "1pkeuh"
		}],
		["line", {
			x1: "12",
			x2: "12.01",
			y1: "16",
			y2: "16",
			key: "4dfq90"
		}]
	],
	aliases: ["alert-circle"]
};
Mr.node;
var Nr = I(Mr), Pr = {
	name: "circle-check",
	size: 24,
	node: [["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}], ["path", {
		d: "m16 9-5.5 5.5L8 12",
		key: "xofnsj"
	}]],
	aliases: ["check-circle-2"]
};
Pr.node;
var Fr = I(Pr), Ir = {
	name: "circle-plus",
	size: 24,
	node: [
		["circle", {
			cx: "12",
			cy: "12",
			r: "10",
			key: "1mglay"
		}],
		["path", {
			d: "M8 12h8",
			key: "1wcyev"
		}],
		["path", {
			d: "M12 8v8",
			key: "napkw2"
		}]
	],
	aliases: ["plus-circle"]
};
Ir.node;
var Lr = I(Ir), Rr = {
	name: "clock",
	size: 24,
	node: [["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}], ["path", {
		d: "M12 6v6l4 2",
		key: "mmk7yg"
	}]]
};
Rr.node;
var zr = I(Rr), Br = {
	name: "construction",
	size: 24,
	node: [
		["rect", {
			x: "2",
			y: "6",
			width: "20",
			height: "8",
			rx: "1",
			key: "1estib"
		}],
		["path", {
			d: "M17 14v7",
			key: "7m2elx"
		}],
		["path", {
			d: "M7 14v7",
			key: "1cm7wv"
		}],
		["path", {
			d: "M17 3v3",
			key: "1v4jwn"
		}],
		["path", {
			d: "M7 3v3",
			key: "7o6guu"
		}],
		["path", {
			d: "M10 14 2.3 6.3",
			key: "1023jk"
		}],
		["path", {
			d: "m14 6 7.7 7.7",
			key: "1s8pl2"
		}],
		["path", {
			d: "m8 6 8 8",
			key: "hl96qh"
		}]
	]
};
Br.node;
var Vr = I(Br), Hr = {
	name: "download",
	size: 24,
	node: [
		["path", {
			d: "M12 15V3",
			key: "m9g1x1"
		}],
		["path", {
			d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
			key: "ih7n3h"
		}],
		["path", {
			d: "m7 10 5 5 5-5",
			key: "brsn70"
		}]
	]
};
Hr.node;
var Ur = I(Hr), Wr = {
	name: "external-link",
	size: 24,
	node: [
		["path", {
			d: "M15 3h6v6",
			key: "1q9fwt"
		}],
		["path", {
			d: "M10 14 21 3",
			key: "gplh6r"
		}],
		["path", {
			d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6",
			key: "a6xqqp"
		}]
	]
};
Wr.node;
var Gr = I(Wr), Kr = {
	name: "eye",
	size: 24,
	node: [["path", {
		d: "M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0",
		key: "1nclc0"
	}], ["circle", {
		cx: "12",
		cy: "12",
		r: "3",
		key: "1v7zrd"
	}]]
};
Kr.node;
var qr = I(Kr), Jr = {
	name: "file-check-corner",
	size: 24,
	node: [
		["path", {
			d: "M10.5 22H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.706.706l3.588 3.588A2.4 2.4 0 0 1 20 8v6",
			key: "g5mvt7"
		}],
		["path", {
			d: "M14 2v5a1 1 0 0 0 1 1h5",
			key: "wfsgrz"
		}],
		["path", {
			d: "m14 20 2 2 4-4",
			key: "15kota"
		}]
	],
	aliases: ["file-check-2"]
};
Jr.node;
var Yr = I(Jr), Xr = {
	name: "file-down",
	size: 24,
	node: [
		["path", {
			d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
			key: "1oefj6"
		}],
		["path", {
			d: "M14 2v5a1 1 0 0 0 1 1h5",
			key: "wfsgrz"
		}],
		["path", {
			d: "M12 18v-6",
			key: "17g6i2"
		}],
		["path", {
			d: "m9 15 3 3 3-3",
			key: "1npd3o"
		}]
	]
};
Xr.node;
var Zr = I(Xr), Qr = {
	name: "file-exclamation-point",
	size: 24,
	node: [
		["path", {
			d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
			key: "1oefj6"
		}],
		["path", {
			d: "M12 9v4",
			key: "juzpu7"
		}],
		["path", {
			d: "M12 17h.01",
			key: "p32p05"
		}]
	],
	aliases: ["file-warning"]
};
Qr.node;
var $r = I(Qr), ei = {
	name: "file-text",
	size: 24,
	node: [
		["path", {
			d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
			key: "1oefj6"
		}],
		["path", {
			d: "M14 2v5a1 1 0 0 0 1 1h5",
			key: "wfsgrz"
		}],
		["path", {
			d: "M10 9H8",
			key: "b1mrlr"
		}],
		["path", {
			d: "M16 13H8",
			key: "t4e002"
		}],
		["path", {
			d: "M16 17H8",
			key: "z1uh3a"
		}]
	]
};
ei.node;
var ti = I(ei), ni = {
	name: "handshake",
	size: 24,
	node: [
		["path", {
			d: "m11 17 2 2a1 1 0 1 0 3-3",
			key: "efffak"
		}],
		["path", {
			d: "m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4",
			key: "9pr0kb"
		}],
		["path", {
			d: "m21 3 1 11h-2",
			key: "1tisrp"
		}],
		["path", {
			d: "M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3",
			key: "1uvwmv"
		}],
		["path", {
			d: "M3 4h8",
			key: "1ep09j"
		}]
	]
};
ni.node;
var ri = I(ni), ii = {
	name: "info",
	size: 24,
	node: [
		["circle", {
			cx: "12",
			cy: "12",
			r: "10",
			key: "1mglay"
		}],
		["path", {
			d: "M12 16v-4",
			key: "1dtifu"
		}],
		["path", {
			d: "M12 8h.01",
			key: "e9boi3"
		}]
	]
};
ii.node;
var ai = I(ii), oi = {
	name: "languages",
	size: 24,
	node: [
		["path", {
			d: "m5 8 6 6",
			key: "1wu5hv"
		}],
		["path", {
			d: "m4 14 6-6 2-3",
			key: "1k1g8d"
		}],
		["path", {
			d: "M2 5h12",
			key: "or177f"
		}],
		["path", {
			d: "M7 2h1",
			key: "1t2jsx"
		}],
		["path", {
			d: "m22 22-5-10-5 10",
			key: "don7ne"
		}],
		["path", {
			d: "M14 18h6",
			key: "1m8k6r"
		}]
	]
};
oi.node;
var si = I(oi), ci = {
	name: "layout-dashboard",
	size: 24,
	node: [
		["rect", {
			width: "7",
			height: "9",
			x: "3",
			y: "3",
			rx: "1",
			key: "10lvy0"
		}],
		["rect", {
			width: "7",
			height: "5",
			x: "14",
			y: "3",
			rx: "1",
			key: "16une8"
		}],
		["rect", {
			width: "7",
			height: "9",
			x: "14",
			y: "12",
			rx: "1",
			key: "1hutg5"
		}],
		["rect", {
			width: "7",
			height: "5",
			x: "3",
			y: "16",
			rx: "1",
			key: "ldoo1y"
		}]
	]
};
ci.node;
var li = I(ci), ui = {
	name: "link-2",
	size: 24,
	node: [
		["path", {
			d: "M9 17H7A5 5 0 0 1 7 7h2",
			key: "8i5ue5"
		}],
		["path", {
			d: "M15 7h2a5 5 0 1 1 0 10h-2",
			key: "1b9ql8"
		}],
		["line", {
			x1: "8",
			x2: "16",
			y1: "12",
			y2: "12",
			key: "1jonct"
		}]
	]
};
ui.node;
var di = I(ui), fi = {
	name: "list-filter",
	size: 24,
	node: [
		["path", {
			d: "M2 5h20",
			key: "1fs1ex"
		}],
		["path", {
			d: "M6 12h12",
			key: "8npq4p"
		}],
		["path", {
			d: "M9 19h6",
			key: "456am0"
		}]
	]
};
fi.node;
var pi = I(fi), mi = {
	name: "map-pin",
	size: 24,
	node: [["path", {
		d: "M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",
		key: "1r0f0z"
	}], ["circle", {
		cx: "12",
		cy: "10",
		r: "3",
		key: "ilqhr7"
	}]]
};
mi.node;
var hi = I(mi), gi = {
	name: "menu",
	size: 24,
	node: [
		["path", {
			d: "M4 5h16",
			key: "1tepv9"
		}],
		["path", {
			d: "M4 12h16",
			key: "1lakjw"
		}],
		["path", {
			d: "M4 19h16",
			key: "1djgab"
		}]
	]
};
gi.node;
var _i = I(gi), vi = {
	name: "octagon-alert",
	size: 24,
	node: [
		["path", {
			d: "M12 16h.01",
			key: "1drbdi"
		}],
		["path", {
			d: "M12 8v4",
			key: "1got3b"
		}],
		["path", {
			d: "M15.312 2a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586l-4.688-4.688A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2z",
			key: "1fd625"
		}]
	],
	aliases: ["alert-octagon"]
};
vi.node;
var yi = I(vi), bi = {
	name: "package-check",
	size: 24,
	node: [
		["path", {
			d: "M12 22V12",
			key: "d0xqtd"
		}],
		["path", {
			d: "m16 17 2 2 4-4",
			key: "uh5qu3"
		}],
		["path", {
			d: "M21 11.127V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.729l7 4a2 2 0 0 0 2 .001l1.32-.753",
			key: "kpkbpo"
		}],
		["path", {
			d: "M3.29 7 12 12l8.71-5",
			key: "19ckod"
		}],
		["path", {
			d: "m7.5 4.27 8.997 5.148",
			key: "9yrvtv"
		}]
	]
};
bi.node;
var xi = I(bi), Si = {
	name: "package",
	size: 24,
	node: [
		["path", {
			d: "M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z",
			key: "1a0edw"
		}],
		["path", {
			d: "M12 22V12",
			key: "d0xqtd"
		}],
		["polyline", {
			points: "3.29 7 12 12 20.71 7",
			key: "ousv84"
		}],
		["path", {
			d: "m7.5 4.27 9 5.15",
			key: "1c824w"
		}]
	]
};
Si.node;
var Ci = I(Si), wi = {
	name: "pen-line",
	size: 24,
	node: [["path", {
		d: "M13 21h8",
		key: "1jsn5i"
	}], ["path", {
		d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
		key: "1a8usu"
	}]],
	aliases: ["edit-3"]
};
wi.node;
var Ti = I(wi), Ei = {
	name: "phone",
	size: 24,
	node: [["path", {
		d: "M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384",
		key: "9njp5v"
	}]]
};
Ei.node;
var Di = I(Ei), Oi = {
	name: "plus",
	size: 24,
	node: [["path", {
		d: "M5 12h14",
		key: "1ays0h"
	}], ["path", {
		d: "M12 5v14",
		key: "s699le"
	}]]
};
Oi.node;
var ki = I(Oi), Ai = {
	name: "scale",
	size: 24,
	node: [
		["path", {
			d: "M12 3v18",
			key: "108xh3"
		}],
		["path", {
			d: "m19 8 3 8a5 5 0 0 1-6 0zV7",
			key: "zcdpyk"
		}],
		["path", {
			d: "M3 7h1a17 17 0 0 0 8-2 17 17 0 0 0 8 2h1",
			key: "1yorad"
		}],
		["path", {
			d: "m5 8 3 8a5 5 0 0 1-6 0zV7",
			key: "eua70x"
		}],
		["path", {
			d: "M7 21h10",
			key: "1b0cd5"
		}]
	]
};
Ai.node;
var ji = I(Ai), Mi = {
	name: "search",
	size: 24,
	node: [["path", {
		d: "m21 21-4.34-4.34",
		key: "14j7rj"
	}], ["circle", {
		cx: "11",
		cy: "11",
		r: "8",
		key: "4ej97u"
	}]]
};
Mi.node;
var Ni = I(Mi), Pi = {
	name: "shield-check",
	size: 24,
	node: [["path", {
		d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
		key: "oel41y"
	}], ["path", {
		d: "m9 12 2 2 4-4",
		key: "dzmm74"
	}]]
};
Pi.node;
var Fi = I(Pi), L = {
	name: "sliders-horizontal",
	size: 24,
	node: [
		["path", {
			d: "M10 5H3",
			key: "1qgfaw"
		}],
		["path", {
			d: "M12 19H3",
			key: "yhmn1j"
		}],
		["path", {
			d: "M14 3v4",
			key: "1sua03"
		}],
		["path", {
			d: "M16 17v4",
			key: "1q0r14"
		}],
		["path", {
			d: "M21 12h-9",
			key: "1o4lsq"
		}],
		["path", {
			d: "M21 19h-5",
			key: "1rlt1p"
		}],
		["path", {
			d: "M21 5h-7",
			key: "1oszz2"
		}],
		["path", {
			d: "M8 10v4",
			key: "tgpxqk"
		}],
		["path", {
			d: "M8 12H3",
			key: "a7s4jb"
		}]
	]
};
L.node;
var R = I(L), Ii = {
	name: "sparkles",
	size: 24,
	node: [
		["path", {
			d: "M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z",
			key: "1s2grr"
		}],
		["path", {
			d: "M20 2v4",
			key: "1rf3ol"
		}],
		["path", {
			d: "M22 4h-4",
			key: "gwowj6"
		}],
		["circle", {
			cx: "4",
			cy: "20",
			r: "2",
			key: "6kqj1y"
		}]
	],
	aliases: ["stars"]
};
Ii.node;
var Li = I(Ii), Ri = {
	name: "stamp",
	size: 24,
	node: [
		["path", {
			d: "M14 13V8.5C14 7 15 7 15 5a3 3 0 0 0-6 0c0 2 1 2 1 3.5V13",
			key: "i9gjdv"
		}],
		["path", {
			d: "M20 15.5a2.5 2.5 0 0 0-2.5-2.5h-11A2.5 2.5 0 0 0 4 15.5V17a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1z",
			key: "1vzg3v"
		}],
		["path", {
			d: "M5 22h14",
			key: "ehvnwv"
		}]
	]
};
Ri.node;
var zi = I(Ri), Bi = {
	name: "trash",
	size: 24,
	node: [
		["path", {
			d: "M10 11v6",
			key: "nco0om"
		}],
		["path", {
			d: "M14 11v6",
			key: "outv1u"
		}],
		["path", {
			d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6",
			key: "miytrc"
		}],
		["path", {
			d: "M3 6h18",
			key: "d0wm0j"
		}],
		["path", {
			d: "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2",
			key: "e791ji"
		}]
	],
	aliases: ["trash-2"]
};
Bi.node;
var Vi = I(Bi), Hi = {
	name: "triangle-alert",
	size: 24,
	node: [
		["path", {
			d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
			key: "wmoenq"
		}],
		["path", {
			d: "M12 9v4",
			key: "juzpu7"
		}],
		["path", {
			d: "M12 17h.01",
			key: "p32p05"
		}]
	],
	aliases: ["alert-triangle"]
};
Hi.node;
var Ui = I(Hi), Wi = {
	name: "truck",
	size: 24,
	node: [
		["path", {
			d: "M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2",
			key: "wrbu53"
		}],
		["path", {
			d: "M15 18H9",
			key: "1lyqi6"
		}],
		["path", {
			d: "M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14",
			key: "lysw3i"
		}],
		["circle", {
			cx: "17",
			cy: "18",
			r: "2",
			key: "332jqn"
		}],
		["circle", {
			cx: "7",
			cy: "18",
			r: "2",
			key: "19iecd"
		}]
	]
};
Wi.node;
var Gi = I(Wi), Ki = {
	name: "upload",
	size: 24,
	node: [
		["path", {
			d: "M12 3v12",
			key: "1x0j5s"
		}],
		["path", {
			d: "m17 8-5-5-5 5",
			key: "7q97r8"
		}],
		["path", {
			d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",
			key: "ih7n3h"
		}]
	]
};
Ki.node;
var qi = I(Ki), Ji = {
	name: "users",
	size: 24,
	node: [
		["path", {
			d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",
			key: "1yyitq"
		}],
		["path", {
			d: "M16 3.128a4 4 0 0 1 0 7.744",
			key: "16gr8j"
		}],
		["path", {
			d: "M22 21v-2a4 4 0 0 0-3-3.87",
			key: "kshegd"
		}],
		["circle", {
			cx: "9",
			cy: "7",
			r: "4",
			key: "nufk8"
		}]
	]
};
Ji.node;
var Yi = I(Ji), Xi = {
	name: "wallet",
	size: 24,
	node: [["path", {
		d: "M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1",
		key: "18etb6"
	}], ["path", {
		d: "M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4",
		key: "xoc0q4"
	}]]
};
Xi.node;
var Zi = I(Xi), Qi = {
	name: "x",
	size: 24,
	node: [["path", {
		d: "M18 6 6 18",
		key: "1bl5f8"
	}], ["path", {
		d: "m6 6 12 12",
		key: "d8bk6v"
	}]]
};
Qi.node;
var $i = I(Qi), ea = {
	ADMIN: "Quản trị",
	SUPPORT: "Điều phối",
	SALE: "Kinh doanh"
}, ta = [
	{
		group: "VẬN HÀNH",
		items: [
			{
				to: "/",
				label: "Tổng Quan Công Việc",
				icon: "layout"
			},
			{
				to: "/viec-can-xu-ly",
				label: "Việc Cần Xử Lý",
				icon: "alarm"
			},
			{
				to: "/lo-hang",
				label: "Lô Hàng",
				icon: "box"
			},
			{
				to: "/tao-lo-moi",
				label: "Tạo Lô Mới",
				icon: "plus"
			},
			{
				to: "/theo-doi",
				label: "Theo Dõi Vận Chuyển",
				icon: "truck"
			}
		]
	},
	{
		group: "KINH DOANH & ĐỐI TÁC",
		items: [
			{
				to: "/khach-hang",
				label: "Khách Hàng",
				icon: "users"
			},
			{
				to: "/ngu-canh-doi-tac",
				label: "Ngữ cảnh Đối tác",
				icon: "handshake"
			},
			{
				to: "/kinh-doanh-bao-gia",
				label: "Kinh doanh · Báo giá",
				icon: "calc"
			},
			{
				to: "/thoa-thuan-ban-giao",
				label: "Thỏa thuận mua bán",
				icon: "filecheck"
			},
			{
				to: "/hop-dong",
				label: "Hợp đồng",
				icon: "filetext"
			}
		]
	},
	{
		group: "TÀI CHÍNH & ĐỐI SOÁT",
		items: [
			{
				to: "/tai-chinh/thu-tien",
				label: "Thu tiền",
				icon: "wallet"
			},
			{
				to: "/tai-chinh/doi-soat",
				label: "Đối soát",
				icon: "scale"
			},
			{
				to: "/tai-chinh/cong-no-doi-tac",
				label: "Công nợ đối tác",
				icon: "building"
			},
			{
				to: "/bao-cao-ceo",
				label: "Báo cáo CEO",
				icon: "chart"
			}
		]
	},
	{
		group: "CÔNG CỤ",
		items: [
			{
				to: "/tra-cuu-thue",
				label: "Tra cứu thuế / HS",
				icon: "search"
			},
			{
				to: "/so-tay",
				label: "Sổ tay",
				icon: "book"
			},
			{
				to: "/dich-thuat",
				label: "Dịch thuật",
				icon: "lang"
			}
		]
	},
	{
		group: "QUẢN TRỊ",
		items: [{
			to: "/nguoi-dung",
			label: "Người dùng & Vai trò",
			icon: "shield"
		}]
	}
], z = {
	shipments: [],
	contracts: [],
	customers: [],
	quotes: [],
	tasks: [],
	notifs: []
};
function na(e, t) {
	e.length = 0, Array.isArray(t) && e.push(...t);
}
C(() => {
	let e = S();
	e && (na(z.shipments, e.shipments), na(z.contracts, e.contracts), na(z.customers, e.customers), na(z.quotes, e.quotes), na(z.tasks, e.tasks), na(z.notifs, e.notifications));
});
{
	let e = S();
	e && (na(z.shipments, e.shipments), na(z.contracts, e.contracts), na(z.customers, e.customers), na(z.quotes, e.quotes), na(z.tasks, e.tasks), na(z.notifs, e.notifications));
}
var ra = z.shipments, ia = z.contracts, aa = z.customers, oa = z.quotes, sa = z.tasks;
z.notifs;
//#endregion
//#region src/lib/format.ts
function B(...e) {
	return e.filter(Boolean).join(" ");
}
function ca(e) {
	return e == null || e === "" || typeof e == "number" && Number.isNaN(e);
}
function la(e, t) {
	if (ca(e)) return "—";
	let n = Number(e);
	return Number.isNaN(n) ? "—" : n.toLocaleString("vi-VN");
}
function ua(e) {
	return ca(e) ? "— ₫" : `${la(e)} ₫`;
}
function da(e, t) {
	let n = (t || "VND").toUpperCase();
	return ca(e) ? `— ${n}` : `${la(e)} ${n}`;
}
function fa(e, t) {
	let n = (t || "VND").toUpperCase();
	return ca(e) ? `— tr ${n}` : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr ${n}`;
}
function pa(e) {
	return ca(e) ? "—" : `${Number(e).toLocaleString("vi-VN", { maximumFractionDigits: 2 })}%`;
}
function ma(e) {
	return ca(e) ? "— tr" : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr`;
}
function ha(e) {
	if (ca(e)) return "—";
	let t = Number(e);
	return Number.isNaN(t) ? String(e) : t.toLocaleString("vi-VN");
}
function V(e) {
	let t = (e ?? "").trim();
	return t.length > 0 ? t : "—";
}
function ga(e, t, n) {
	if (!t) return;
	let r = atob(t), i = new Uint8Array(r.length);
	for (let e = 0; e < r.length; e += 1) i[e] = r.charCodeAt(e);
	let a = new Blob([i], { type: n }), o = URL.createObjectURL(a), s = document.createElement("a");
	s.href = o, s.download = e, document.body.appendChild(s), s.click(), document.body.removeChild(s), setTimeout(() => URL.revokeObjectURL(o), 4e3);
}
//#endregion
//#region src/components/ui.tsx
var _a = {
	layout: li,
	alarm: yr,
	box: Ci,
	plus: Lr,
	truck: Gi,
	users: Yi,
	handshake: ri,
	calc: Dr,
	filecheck: Yr,
	filetext: ti,
	wallet: Zi,
	scale: ji,
	building: Tr,
	chart: kr,
	search: Ni,
	book: Cr,
	lang: si,
	shield: Fi
};
function H({ tone: e, children: t, size: n = "md" }) {
	return /* @__PURE__ */ (0, F.jsx)("span", {
		className: B("inline-flex items-center gap-1.5 font-semibold border rounded-full whitespace-nowrap", n === "sm" ? "text-[12.5px] px-2.5 py-1" : "text-[13.5px] px-3 py-1.5", {
			green: "bg-emerald-50 text-emerald-800 border-emerald-200",
			amber: "bg-amber-50 text-amber-900 border-amber-200",
			red: "bg-red-50 text-red-800 border-red-200",
			blue: "bg-blue-50 text-blue-800 border-blue-200",
			gray: "bg-slate-100 text-slate-700 border-slate-200"
		}[e]),
		children: t
	});
}
function va({ tone: e }) {
	return /* @__PURE__ */ (0, F.jsx)("span", { className: B("inline-block w-2.5 h-2.5 rounded-full shrink-0", {
		green: "bg-emerald-500",
		amber: "bg-amber-500",
		red: "bg-red-500",
		blue: "bg-blue-500",
		gray: "bg-slate-400"
	}[e] ?? "bg-slate-400") });
}
function ya({ icon: e, title: t, sub: n, right: r }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "flex items-start justify-between gap-3 mb-3",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-2.5",
			children: [e && /* @__PURE__ */ (0, F.jsx)("span", {
				className: "mt-0.5 w-9 h-9 rounded-xl bg-[#0f2a4a] text-white grid place-items-center shrink-0",
				children: e
			}), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("h2", {
				className: "text-[17px] md:text-[19px] font-800 font-extrabold text-[#0f2a4a] leading-tight",
				children: t
			}), n && /* @__PURE__ */ (0, F.jsx)("p", {
				className: "text-[13.5px] text-slate-500 mt-0.5",
				children: n
			})] })]
		}), r]
	});
}
function U({ label: e, required: t, hint: n, error: r, children: i }) {
	return /* @__PURE__ */ (0, F.jsxs)("label", {
		className: "block",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("span", {
				className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
				children: [
					e,
					" ",
					t && /* @__PURE__ */ (0, F.jsx)("span", {
						className: "text-red-600 font-bold",
						children: "*"
					})
				]
			}),
			i,
			n && !r && /* @__PURE__ */ (0, F.jsx)("span", {
				className: "block text-[13px] text-slate-500 mt-1",
				children: n
			}),
			r && /* @__PURE__ */ (0, F.jsxs)("span", {
				className: "block text-[13.5px] text-red-700 font-medium mt-1",
				children: ["⚠ ", r]
			})
		]
	});
}
var W = (e) => B("w-full rounded-xl border-2 bg-white px-3.5 text-[15.5px] min-h-[48px] py-2.5 placeholder:text-slate-400 transition-colors", e === "missing" && "border-amber-400 bg-amber-50/60", e === "invalid" && "border-red-400 bg-red-50/60", (!e || e === "ok") && "border-slate-200 focus:border-[#1e5aa8]");
function ba({ children: e, onClick: t, className: n, disabled: r }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		disabled: r,
		className: B("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] hover:bg-[#14365e] text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-navy-900/20 disabled:opacity-50 disabled:cursor-not-allowed", n),
		children: e
	});
}
function xa({ children: e, onClick: t, className: n }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		className: B("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-emerald-600/25", n),
		children: e
	});
}
function Sa({ children: e, onClick: t, className: n, danger: r }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		className: B("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 font-semibold text-[15px] px-4 min-h-[48px] bg-white", r ? "border-red-200 text-red-700 hover:bg-red-50" : "border-slate-200 text-[#0f2a4a] hover:bg-slate-50", n),
		children: e
	});
}
function Ca({ tone: e = "amber", title: t, desc: n, action: r, onAction: i }) {
	let a = {
		amber: "border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50/60",
		red: "border-red-300 bg-gradient-to-r from-red-50 to-orange-50/60",
		green: "border-emerald-300 bg-gradient-to-r from-emerald-50 to-teal-50/60",
		blue: "border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50/60"
	}, o = e === "red" ? yi : e === "green" ? Fr : e === "blue" ? ai : Ui, s = e === "red" ? "bg-red-600" : e === "green" ? "bg-emerald-600" : e === "blue" ? "bg-blue-600" : "bg-amber-500";
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: B("rounded-2xl border-2 p-4 md:p-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-4", a[e]),
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-3 flex-1 min-w-0",
			children: [/* @__PURE__ */ (0, F.jsx)("span", {
				className: B("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", s),
				children: /* @__PURE__ */ (0, F.jsx)(o, { size: 22 })
			}), /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "min-w-0",
				children: [
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[12.5px] font-bold uppercase tracking-wide text-slate-500",
						children: "Việc tiếp theo"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[16px] md:text-[18px] font-extrabold text-[#0f2a4a] leading-snug",
						children: t
					}),
					n && /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-600 mt-1",
						children: n
					})
				]
			})]
		}), r && /* @__PURE__ */ (0, F.jsxs)("button", {
			onClick: i,
			className: "btn-press touch-target shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[15.5px] px-6 min-h-[52px] shadow-lg w-full md:w-auto",
			children: [
				r,
				" ",
				/* @__PURE__ */ (0, F.jsx)(hr, { size: 18 })
			]
		})]
	});
}
function wa({ what: e, where: t, actionLabel: n, onAction: r }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-xl border-2 border-dashed border-amber-400 bg-amber-50 p-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-2 flex-1",
			children: [/* @__PURE__ */ (0, F.jsx)(Nr, {
				size: 20,
				className: "text-amber-600 shrink-0 mt-0.5"
			}), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "font-bold text-[15px] text-amber-900",
				children: ["Thiếu ", e]
			}), t && /* @__PURE__ */ (0, F.jsx)("p", {
				className: "text-[13.5px] text-amber-800",
				children: t
			})] })]
		}), /* @__PURE__ */ (0, F.jsxs)("button", {
			onClick: r,
			className: "btn-press touch-target inline-flex items-center justify-center gap-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-[14.5px] font-bold px-4 min-h-[44px] whitespace-nowrap",
			children: [
				/* @__PURE__ */ (0, F.jsx)(Ti, { size: 16 }),
				" ",
				n
			]
		})]
	});
}
function Ta({ label: e, value: t, big: n }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "flex items-start justify-between gap-3 py-2 border-b border-slate-100 last:border-0",
		children: [/* @__PURE__ */ (0, F.jsx)("span", {
			className: "text-[13.5px] text-slate-500 font-medium shrink-0 pt-0.5",
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("span", {
			className: B("text-right font-semibold text-slate-800", n ? "text-[17px]" : "text-[14.5px]"),
			children: t
		})]
	});
}
//#endregion
//#region src/components/Layout.tsx
function Ea() {
	return /* @__PURE__ */ (0, F.jsxs)(P, {
		to: "/",
		className: "flex items-center gap-2.5 shrink-0",
		children: [
			/* @__PURE__ */ (0, F.jsx)("span", {
				className: "w-10 h-10 rounded-xl bg-gradient-to-br from-[#1e5aa8] to-[#0a1f3a] grid place-items-center text-white font-extrabold text-[18px] shadow",
				children: "T"
			}),
			/* @__PURE__ */ (0, F.jsxs)("span", {
				className: "leading-tight hidden sm:block",
				children: [/* @__PURE__ */ (0, F.jsx)("span", {
					className: "block font-extrabold text-[14.5px] text-[#0f2a4a]",
					children: "TRƯỜNG THÀNH"
				}), /* @__PURE__ */ (0, F.jsx)("span", {
					className: "block text-[11.5px] text-slate-500 font-medium",
					children: "Phú Anh Logistics · Nội bộ"
				})]
			}),
			/* @__PURE__ */ (0, F.jsx)("span", {
				className: "text-[11px] font-extrabold tracking-wider bg-violet-100 text-violet-800 border border-violet-300 rounded-md px-1.5 py-0.5 ml-1",
				children: "PROTOTYPE"
			})
		]
	});
}
function Da({ children: e }) {
	let { role: t, setRole: n, userName: r, query: i, setQuery: a, searchOpen: o, setSearchOpen: s, navOpen: c, setNavOpen: l, notifOpen: u, setNotifOpen: d, quickAddOpen: f, setQuickAddOpen: p, toasts: m, dismissToast: h, toast: g, notifications: v } = Xn(), y = v, b = y.length, x = xt(), S = vt(), [C, w] = (0, _.useState)(!1), T = (0, _.useMemo)(() => {
		let e = i.trim().toLowerCase();
		return e.length < 2 ? null : {
			lots: ra.filter((t) => (t.id + t.customer + t.contract + t.route).toLowerCase().includes(e)).slice(0, 4),
			cts: ia.filter((t) => (t.id + t.company + t.agent).toLowerCase().includes(e)).slice(0, 3),
			cus: aa.filter((t) => (t.name + t.mst).toLowerCase().includes(e)).slice(0, 3),
			quo: oa.filter((t) => (t.id + t.customer).toLowerCase().includes(e)).slice(0, 2)
		};
	}, [i]), E = (e) => {
		s(!1), a(""), x(e), l(!1);
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "min-h-screen flex flex-col",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("header", {
				className: "no-print sticky top-0 z-40 bg-white border-b border-slate-200 shadow-[0_1px_12px_rgba(15,42,74,.08)]",
				children: [/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex items-center gap-2 md:gap-4 px-3 md:px-5 h-[64px] max-w-[1600px] mx-auto",
					children: [
						/* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => l(!0),
							className: "lg:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Mở menu",
							children: /* @__PURE__ */ (0, F.jsx)(_i, {
								size: 22,
								className: "text-[#0f2a4a]"
							})
						}),
						/* @__PURE__ */ (0, F.jsx)(Ea, {}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "hidden md:flex flex-1 max-w-[560px] mx-auto relative",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center w-full rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ni, {
										size: 19,
										className: "ml-3.5 text-slate-400 shrink-0"
									}),
									/* @__PURE__ */ (0, F.jsx)("input", {
										value: i,
										onChange: (e) => a(e.target.value),
										onFocus: () => s(!0),
										placeholder: "Tìm mã lô · khách hàng · hợp đồng · container · báo giá…",
										className: "w-full bg-transparent px-3 py-2.5 text-[15px] outline-none placeholder:text-slate-400"
									}),
									i && /* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => a(""),
										className: "mr-2 w-8 h-8 grid place-items-center rounded-lg hover:bg-slate-200",
										children: /* @__PURE__ */ (0, F.jsx)($i, { size: 16 })
									})
								]
							}), o && T && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "absolute top-[52px] left-0 right-0 bg-white rounded-2xl border border-slate-200 shadow-2xl p-2 z-50 anim-slide-up max-h-[70vh] overflow-auto",
								children: [
									T.lots.length + T.cts.length + T.cus.length + T.quo.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "p-4 text-[14.5px] text-slate-500",
										children: [
											"Không tìm thấy “",
											i,
											"”. Thử mã lô ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "LO-0306" }),
											", ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "An Phát" }),
											" hoặc ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "HDMB" }),
											"."
										]
									}),
									T.lots.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => E(`/lo-hang/${e.id}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-blue-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(Ci, {
												size: 17,
												className: "text-blue-700"
											})
										}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.customer
											]
										}), /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Lô hàng — ", e.status]
										})] })]
									}, e.id)),
									T.cts.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => E(`/hop-dong/${e.id}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-emerald-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(ti, {
												size: 17,
												className: "text-emerald-700"
											})
										}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.company
											]
										}), /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Hợp đồng — ", e.status]
										})] })]
									}, e.id)),
									T.cus.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => E("/khach-hang"),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-amber-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(Gi, {
												size: 17,
												className: "text-amber-700"
											})
										}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.short,
												" · MST ",
												e.mst
											]
										}), /* @__PURE__ */ (0, F.jsx)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: "Khách hàng"
										})] })]
									}, e.mst)),
									T.quo.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => E("/kinh-doanh-bao-gia"),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-violet-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(Dr, {
												size: 17,
												className: "text-violet-700"
											})
										}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.customer
											]
										}), /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Báo giá — ", e.status]
										})] })]
									}, e.id)),
									/* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => s(!1),
										className: "w-full text-center py-2 text-[13px] text-slate-400 font-medium",
										children: "Nhấn ra ngoài để đóng"
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", { className: "flex-1 md:hidden" }),
						/* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => s(!o),
							className: "md:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Tìm kiếm",
							children: /* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 21,
								className: "text-[#0f2a4a]"
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "relative hidden sm:block",
							children: [/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => w((e) => !e),
								className: "flex items-center gap-2 rounded-xl border-2 border-slate-200 pl-1.5 pr-2.5 py-1 hover:border-[#1e5aa8]",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: B("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", t === "ADMIN" ? "bg-violet-600" : t === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600"),
									children: r.charAt(0)
								}), /* @__PURE__ */ (0, F.jsxs)("span", {
									className: "text-left leading-tight",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[13px] font-bold text-[#0f2a4a]",
										children: r
									}), /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block text-[11.5px] text-slate-500",
										children: [
											ea[t],
											" · ",
											t
										]
									})]
								})]
							}), C && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "absolute right-0 top-[52px] w-[260px] bg-white rounded-2xl border shadow-2xl p-2 z-50 anim-slide-up",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "px-3 pt-2 pb-1 text-[12px] font-bold uppercase tracking-wide text-slate-400",
									children: "Chuyển vai trò (prototype)"
								}), [
									"ADMIN",
									"SUPPORT",
									"SALE"
								].map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => {
										n(e), w(!1), g(`Đã chuyển sang vai trò ${ea[e]}`, e === "ADMIN" ? "Xem được hợp đồng, tài chính & người dùng" : e === "SUPPORT" ? "Ưu tiên điều phối lô hàng & chứng từ" : "Ưu tiên khách hàng, báo giá & hợp đồng", "blue");
									},
									className: B("w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between hover:bg-slate-50", t === e && "bg-blue-50"),
									children: [/* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block font-bold text-[14.5px]",
										children: ea[e]
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[12px] text-slate-500",
										children: e
									})] }), t === e && /* @__PURE__ */ (0, F.jsx)("span", {
										className: "text-blue-700 font-bold text-[13px]",
										children: "● Đang dùng"
									})]
								}, e))]
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => d(!0),
							className: "relative touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Thông báo",
							children: [/* @__PURE__ */ (0, F.jsx)(xr, {
								size: 21,
								className: "text-[#0f2a4a]"
							}), b > 0 && /* @__PURE__ */ (0, F.jsx)("span", {
								className: "absolute top-1 right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-600 text-white text-[11px] font-extrabold grid place-items-center",
								children: b
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => p(!0),
							className: "hidden md:inline-flex touch-target items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px] hover:bg-[#14365e]",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 18 }), " Thêm"]
						})
					]
				}), o && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "md:hidden px-3 pb-3 anim-slide-up",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center rounded-xl border-2 border-[#1e5aa8] bg-slate-50",
						children: [
							/* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 18,
								className: "ml-3 text-slate-400"
							}),
							/* @__PURE__ */ (0, F.jsx)("input", {
								autoFocus: !0,
								value: i,
								onChange: (e) => a(e.target.value),
								placeholder: "Tìm mã lô · khách · hợp đồng…",
								className: "w-full bg-transparent px-2.5 py-3 text-[15px] outline-none"
							}),
							/* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => {
									s(!1), a("");
								},
								className: "mr-1 w-10 h-10 grid place-items-center",
								children: /* @__PURE__ */ (0, F.jsx)($i, { size: 18 })
							})
						]
					}), T && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-2 bg-white rounded-2xl border shadow-xl divide-y max-h-[50vh] overflow-auto",
						children: [
							T.lots.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => E(`/lo-hang/${e.id}`),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, F.jsx)(Ci, {
									size: 18,
									className: "text-blue-700 shrink-0"
								}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "block font-bold text-[15px]",
									children: [
										e.id,
										" · ",
										e.customer
									]
								}), /* @__PURE__ */ (0, F.jsxs)("span", {
									className: "block text-[13px] text-slate-500",
									children: [
										e.status,
										" — ",
										e.nextAction
									]
								})] })]
							}, e.id)),
							T.cts.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => E(`/hop-dong/${e.id}`),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, F.jsx)(ti, {
									size: 18,
									className: "text-emerald-700 shrink-0"
								}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "block font-bold text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsxs)("span", {
									className: "block text-[13px] text-slate-500",
									children: [
										e.company,
										" — ",
										e.status
									]
								})] })]
							}, e.id)),
							T.lots.length + T.cts.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "p-4 text-[14px] text-slate-500",
								children: "Không tìm thấy. Thử “LO-0306” hoặc “An Phát”."
							})
						]
					})]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex flex-1 max-w-[1600px] w-full mx-auto",
				children: [
					/* @__PURE__ */ (0, F.jsx)("aside", {
						className: "no-print hidden lg:block w-[264px] shrink-0 border-r border-slate-200 bg-white min-h-[calc(100vh-64px)] sticky top-[64px] self-start max-h-[calc(100vh-64px)] overflow-y-auto",
						children: /* @__PURE__ */ (0, F.jsxs)("nav", {
							className: "p-3 pb-10",
							children: [ta.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "mb-4",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "px-3 mb-1.5 text-[11.5px] font-extrabold tracking-wider text-slate-400",
									children: e.group
								}), e.items.map((e) => {
									let t = _a[e.icon] ?? Ci;
									return /* @__PURE__ */ (0, F.jsxs)(Fn, {
										to: e.to,
										className: ({ isActive: t }) => B("flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14.5px] font-medium mb-0.5 transition-colors", t || e.to !== "/" && S.pathname.startsWith(e.to) ? "bg-[#0f2a4a] text-white shadow-md" : "text-slate-700 hover:bg-slate-100"),
										children: [
											/* @__PURE__ */ (0, F.jsx)(t, {
												size: 19,
												className: "shrink-0"
											}),
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "flex-1",
												children: e.label
											}),
											e.to === "/viec-can-xu-ly" && /* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
												children: "6"
											})
										]
									}, e.to);
								})]
							}, e.group)), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "mx-1 mt-2 rounded-2xl bg-gradient-to-br from-[#0f2a4a] to-[#1e5aa8] text-white p-4",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-bold text-[14px]",
										children: "Cần hỗ trợ thao tác?"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12.5px] text-blue-100 mt-1",
										children: "Sổ tay hướng dẫn từng bước cho Sale & Support mới."
									}),
									/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/so-tay",
										className: "mt-2.5 inline-flex items-center gap-1.5 bg-white text-[#0f2a4a] text-[13.5px] font-bold rounded-lg px-3 py-2",
										children: ["Mở sổ tay ", /* @__PURE__ */ (0, F.jsx)(jr, { size: 15 })]
									})
								]
							})]
						})
					}),
					c && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "no-print fixed inset-0 z-50 lg:hidden",
						children: [/* @__PURE__ */ (0, F.jsx)("div", {
							className: "absolute inset-0 bg-slate-900/50 anim-fade",
							onClick: () => l(!1)
						}), /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "absolute left-0 top-0 bottom-0 w-[300px] max-w-[85vw] bg-white shadow-2xl overflow-y-auto anim-slide-up",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center justify-between p-4 border-b sticky top-0 bg-white z-10",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[#0f2a4a]",
									children: "Menu điều hành"
								}), /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => l(!1),
									className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
									children: /* @__PURE__ */ (0, F.jsx)($i, { size: 20 })
								})]
							}), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "p-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)("div", {
										className: "flex gap-2 mb-3",
										children: [
											"ADMIN",
											"SUPPORT",
											"SALE"
										].map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
											onClick: () => n(e),
											className: B("flex-1 touch-target rounded-xl border-2 text-[13px] font-bold py-2", t === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600"),
											children: e
										}, e))
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "px-2 text-[12px] text-slate-500 mb-2",
										children: [
											"Đang dùng: ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: r }),
											" · ",
											ea[t]
										]
									}),
									ta.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
										className: "mb-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "px-2 mb-1 text-[11px] font-extrabold tracking-wider text-slate-400",
											children: e.group
										}), e.items.map((e) => {
											let t = _a[e.icon] ?? Ci, n = e.to === "/" ? S.pathname === "/" : S.pathname.startsWith(e.to);
											return /* @__PURE__ */ (0, F.jsxs)(Fn, {
												to: e.to,
												onClick: () => l(!1),
												className: B("flex items-center gap-3 px-3 py-3 rounded-xl text-[15px] font-medium mb-0.5", n ? "bg-[#0f2a4a] text-white" : "text-slate-700 hover:bg-slate-100"),
												children: [
													/* @__PURE__ */ (0, F.jsx)(t, {
														size: 20,
														className: "shrink-0"
													}),
													e.label,
													e.to === "/viec-can-xu-ly" && /* @__PURE__ */ (0, F.jsx)("span", {
														className: "ml-auto text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
														children: "6"
													})
												]
											}, e.to);
										})]
									}, e.group))
								]
							})]
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("main", {
						className: "flex-1 min-w-0 px-3 md:px-6 py-4 md:py-6 pb-28 md:pb-10 w-full",
						children: [e, /* @__PURE__ */ (0, F.jsx)("footer", {
							className: "mt-10 text-center text-[12.5px] text-slate-400 pb-4",
							children: "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam · Bản prototype nội bộ — dữ liệu minh họa 09/09/2026"
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsx)("nav", {
				className: "no-print md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,.08)]",
				style: { paddingBottom: "env(safe-area-inset-bottom)" },
				children: /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid grid-cols-5",
					children: [[
						{
							to: "/",
							label: "Tổng quan",
							icon: _a.layout
						},
						{
							to: "/lo-hang",
							label: "Lô hàng",
							icon: Ci
						},
						{
							to: "/hop-dong",
							label: "Hợp đồng",
							icon: ti
						},
						{
							to: "/tai-chinh/thu-tien",
							label: "Tài chính",
							icon: Zi
						}
					].map((e) => {
						let t = e.to === "/" ? S.pathname === "/" : S.pathname.startsWith(e.to), n = e.icon;
						return /* @__PURE__ */ (0, F.jsxs)(Fn, {
							to: e.to,
							className: B("touch-target flex flex-col items-center justify-center gap-0.5 py-2 text-[11.5px] font-semibold", t ? "text-[#0f2a4a]" : "text-slate-400"),
							children: [
								/* @__PURE__ */ (0, F.jsx)(n, {
									size: 22,
									strokeWidth: t ? 2.4 : 1.8
								}),
								e.label,
								t && /* @__PURE__ */ (0, F.jsx)("span", { className: "w-8 h-1 rounded-full bg-[#0f2a4a]" })
							]
						}, e.to);
					}), /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: () => p(!0),
						className: "touch-target flex flex-col items-center justify-center gap-0.5 py-1.5 text-[11.5px] font-semibold text-slate-500",
						children: [/* @__PURE__ */ (0, F.jsx)("span", {
							className: "w-11 h-8 -mt-3 rounded-2xl bg-[#0f2a4a] text-white grid place-items-center shadow-lg",
							children: /* @__PURE__ */ (0, F.jsx)(ki, { size: 22 })
						}), "Thêm"]
					})]
				})
			}),
			u && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "no-print fixed inset-0 z-50",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/50 anim-fade",
					onClick: () => d(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "absolute right-0 top-0 bottom-0 w-[380px] max-w-[92vw] bg-white shadow-2xl flex flex-col anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center justify-between p-4 border-b",
							children: [/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-[16px] text-[#0f2a4a]",
								children: [
									"Thông báo · ",
									b,
									" chưa đọc"
								]
							}), /* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => d(!1),
								className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
								children: /* @__PURE__ */ (0, F.jsx)($i, { size: 20 })
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex-1 overflow-y-auto p-3 space-y-2",
							children: [y.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[14px] text-slate-500 p-4 text-center",
								children: "Không có cảnh báo nào theo dữ liệu hiện tại."
							}), y.map((e) => /* @__PURE__ */ (0, F.jsx)("div", {
								className: "rounded-2xl border border-slate-200 p-3.5 lift",
								children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex items-start gap-2.5",
									children: [/* @__PURE__ */ (0, F.jsx)("span", { className: B("w-2.5 h-2.5 rounded-full mt-1.5 shrink-0", e.tone === "red" ? "bg-red-500 pulse-dot" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500") }), /* @__PURE__ */ (0, F.jsxs)("div", { children: [
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-bold text-[14.5px] text-[#0f2a4a]",
											children: e.title
										}),
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[13.5px] text-slate-600 mt-0.5",
											children: e.desc
										}),
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-slate-400 mt-1",
											children: e.time
										})
									] })]
								})
							}, e.id))]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "p-3 border-t",
							children: /* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => {
									d(!1), x("/viec-can-xu-ly");
								},
								className: "w-full touch-target rounded-xl bg-[#0f2a4a] text-white font-bold py-3",
								children: "Mở Việc Cần Xử Lý"
							})
						})
					]
				})]
			}),
			f && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "no-print fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/50 anim-fade",
					onClick: () => p(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[520px] sm:rounded-3xl rounded-t-3xl p-5 pb-8 anim-slide-up",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, F.jsx)("div", { className: "w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-4 sm:hidden" }),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center justify-between mb-1",
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-extrabold text-[18px] text-[#0f2a4a]",
								children: "Thêm mới nhanh"
							}), /* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => p(!1),
								className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
								children: /* @__PURE__ */ (0, F.jsx)($i, { size: 20 })
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500 mb-4",
							children: "Chọn việc muốn làm — mỗi nút dẫn thẳng tới màn hình nhập liệu."
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-2.5",
							children: [
								{
									label: "Tạo lô hàng mới",
									desc: "Từ báo giá đã chốt hoặc nhập tay",
									to: "/tao-lo-moi",
									icon: Ci,
									bg: "bg-blue-50 text-blue-700"
								},
								{
									label: "Tạo hợp đồng mới",
									desc: "HDMB / HDNT + phụ lục",
									to: "/hop-dong/moi",
									icon: ti,
									bg: "bg-emerald-50 text-emerald-700"
								},
								{
									label: "Tạo báo giá",
									desc: "Dự toán chi phí & giá bán",
									to: "/kinh-doanh-bao-gia",
									icon: Dr,
									bg: "bg-violet-50 text-violet-700"
								},
								{
									label: "Ghi nhận thanh toán",
									desc: "Thu tiền khách / trả đối tác",
									to: "/tai-chinh/thu-tien",
									icon: Zi,
									bg: "bg-amber-50 text-amber-700"
								},
								{
									label: "Tra cứu thuế / HS",
									desc: "Mã HS, thuế NK, VAT",
									to: "/tra-cuu-thue",
									icon: Gi,
									bg: "bg-slate-100 text-slate-700"
								}
							].map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => {
									p(!1), x(e.to);
								},
								className: "touch-target flex items-center gap-3 rounded-2xl border-2 border-slate-100 hover:border-[#1e5aa8] p-3.5 text-left lift bg-white",
								children: [
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: B("w-11 h-11 rounded-xl grid place-items-center shrink-0", e.bg),
										children: /* @__PURE__ */ (0, F.jsx)(e.icon, { size: 21 })
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "flex-1",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "block font-bold text-[15px] text-[#0f2a4a]",
											children: e.label
										}), /* @__PURE__ */ (0, F.jsx)("span", {
											className: "block text-[13px] text-slate-500",
											children: e.desc
										})]
									}),
									/* @__PURE__ */ (0, F.jsx)(jr, {
										size: 19,
										className: "text-slate-300"
									})
								]
							}, e.label))
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "no-print fixed z-[60] left-3 right-3 bottom-[84px] md:left-auto md:right-6 md:bottom-6 md:w-[380px] space-y-2",
				children: m.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "toast-in rounded-2xl bg-[#0f2a4a] text-white p-4 shadow-2xl flex items-start gap-3",
					children: [
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: B("w-9 h-9 rounded-xl grid place-items-center shrink-0", e.tone === "green" ? "bg-emerald-500" : e.tone === "red" ? "bg-red-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500"),
							children: e.tone === "green" ? "✓" : e.tone === "red" ? "!" : e.tone === "amber" ? "⚠" : "i"
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex-1 min-w-0",
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-bold text-[14.5px]",
								children: e.title
							}), e.desc && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] text-blue-100 mt-0.5",
								children: e.desc
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => h(e.id),
							className: "w-8 h-8 grid place-items-center rounded-lg hover:bg-white/10 shrink-0",
							children: /* @__PURE__ */ (0, F.jsx)($i, { size: 16 })
						})
					]
				}, e.id))
			}),
			o && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "fixed inset-0 z-30 hidden md:block",
				onClick: () => s(!1)
			})
		]
	});
}
//#endregion
//#region src/pages/Home.tsx
var Oa = {
	"Lô đang chạy": {
		icon: Gi,
		bg: "bg-slate-600",
		bar: "bg-slate-500"
	},
	"Chờ lấy hàng": {
		icon: xi,
		bg: "bg-slate-600",
		bar: "bg-slate-500"
	},
	"Đang vận chuyển": {
		icon: Gi,
		bg: "bg-blue-600",
		bar: "bg-blue-500"
	},
	"Chờ thông quan": {
		icon: Yr,
		bg: "bg-amber-500",
		bar: "bg-amber-500"
	},
	"Chờ giao": {
		icon: xi,
		bg: "bg-blue-600",
		bar: "bg-blue-500"
	},
	"Đã giao": {
		icon: Yr,
		bg: "bg-emerald-600",
		bar: "bg-emerald-500"
	}
}, ka = {
	icon: $r,
	bg: "bg-red-500",
	bar: "bg-red-500"
};
function Aa() {
	let { shipments: e, home: t, tasks: n, environment: r } = Xn(), i = xt(), a = t?.tiles ?? [], o = t?.focus ?? null, s = t?.summary, c = (n ?? []).slice(0, 3), l = t?.runningSummary ?? [], u = (/* @__PURE__ */ new Date()).toLocaleDateString("vi-VN", {
		weekday: "long",
		day: "2-digit",
		month: "2-digit",
		year: "numeric"
	});
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-5 max-w-[1200px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-3xl bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8] text-white p-5 md:p-7 relative overflow-hidden",
				children: [
					/* @__PURE__ */ (0, F.jsx)("div", { className: "absolute -right-16 -top-16 w-64 h-64 rounded-full bg-white/10" }),
					/* @__PURE__ */ (0, F.jsx)("div", { className: "absolute right-10 bottom-0 w-32 h-32 rounded-full bg-white/5" }),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13px] font-semibold text-blue-200 uppercase tracking-wider",
						children: [u, r?.isSandbox ? ` · ${r.label}` : ""]
					}),
					/* @__PURE__ */ (0, F.jsx)("h1", {
						className: "text-[22px] md:text-[30px] font-extrabold leading-tight mt-1",
						children: "Hôm nay tôi cần làm gì?"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14.5px] md:text-[16px] text-blue-100 mt-1.5 max-w-[640px]",
						children: o ? /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
							t?.urgentCount ?? 0,
							" việc khẩn · bắt đầu từ ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-white",
								children: [
									o.id,
									" — ",
									o.nextAction
								]
							}),
							"."
						] }) : "Không có việc khẩn. Toàn bộ lô hàng đang ổn định."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-wrap gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/viec-can-xu-ly",
							className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]",
							children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 18 })]
						}), o && /* @__PURE__ */ (0, F.jsxs)(P, {
							to: `/lo-hang/${o.id}`,
							className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]",
							children: ["Mở ", o.id]
						})]
					})
				]
			}),
			o && /* @__PURE__ */ (0, F.jsx)(Ca, {
				tone: o.priority === "Khan" ? "red" : "amber",
				title: `${o.id}: ${o.nextAction}`,
				desc: V(o.nextActionDetail),
				action: "XỬ LÝ NGAY",
				onAction: () => {
					i(o.to);
				}
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", { children: [/* @__PURE__ */ (0, F.jsx)(ya, {
				title: "VIỆC TIẾP THEO",
				sub: "Bấm vào từng thẻ để đi thẳng tới màn hình xử lý"
			}), /* @__PURE__ */ (0, F.jsx)("div", {
				className: "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3",
				children: a.map((e) => {
					let t = Oa[e.label] ?? ka, n = t.icon;
					return /* @__PURE__ */ (0, F.jsxs)(P, {
						to: e.to,
						className: "lift btn-press rounded-2xl bg-white border border-slate-200 overflow-hidden flex sm:flex-col min-h-[88px]",
						children: [/* @__PURE__ */ (0, F.jsx)("div", { className: B("w-1.5 sm:w-full sm:h-1.5 shrink-0", t.bar) }), /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "p-3.5 flex items-center sm:items-start gap-3 sm:flex-col sm:gap-2 flex-1",
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: B("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", t.bg),
								children: /* @__PURE__ */ (0, F.jsx)(n, { size: 21 })
							}), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex-1 min-w-0",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2",
										children: [
											e.label,
											" ",
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[12px] font-extrabold bg-red-600 text-white rounded-full min-w-[24px] h-6 px-1.5 grid place-items-center",
												children: e.value
											})
										]
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[13px] text-slate-500 mt-0.5 leading-snug truncate",
										children: e.sub
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "inline-flex items-center gap-1 text-[13.5px] font-bold text-[#1e5aa8] mt-1.5",
										children: ["Xem lô ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
									})
								]
							})]
						})]
					}, e.label);
				})
			})] }),
			/* @__PURE__ */ (0, F.jsxs)("section", { children: [/* @__PURE__ */ (0, F.jsx)(ya, {
				title: "Chỉ số vận hành hôm nay",
				sub: "Chỉ hiện số liệu giúp ra quyết định — bấm để lọc danh sách"
			}), /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3",
				children: [
					a.map((e) => /* @__PURE__ */ (0, F.jsxs)(P, {
						to: e.to,
						className: "lift rounded-2xl bg-white border border-slate-200 p-4",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] font-semibold text-slate-500",
								children: e.label
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[24px] md:text-[28px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5",
								children: e.value
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12.5px] text-slate-400 mt-0.5 truncate",
								children: e.sub
							})
						]
					}, e.label)),
					/* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/tai-chinh/thu-tien",
						className: "lift rounded-2xl bg-emerald-600 text-white p-4",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] font-semibold text-emerald-100",
								children: "Phải thu còn lại"
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[24px] md:text-[26px] font-extrabold leading-tight mt-0.5",
								children: ma(t?.outstandingTotal)
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-emerald-100 mt-0.5",
								children: [t?.outstandingCount ?? 0, " lô còn công nợ"]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/tai-chinh/doi-soat",
						className: "lift rounded-2xl bg-white border-2 border-amber-300 p-4",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] font-semibold text-slate-500",
								children: "Cần đối soát tài chính"
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[24px] md:text-[26px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5",
								children: s?.financialAttention ?? 0
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12.5px] text-amber-700 font-semibold mt-0.5",
								children: "Theo Shipment 360"
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/viec-can-xu-ly",
						className: "lift rounded-2xl bg-red-600 text-white p-4 col-span-2 md:col-span-1",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] font-semibold text-red-100",
								children: "Việc quá hạn / khẩn"
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[24px] md:text-[28px] font-extrabold leading-tight mt-0.5",
								children: [(s?.critical ?? 0) + (t?.urgentCount ?? 0), " việc"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-red-100 mt-0.5",
								children: [s?.deadlineSoon ?? 0, " lô sắp tới hạn khách"]
							})
						]
					})
				]
			})] }),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center justify-between mb-3",
						children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(zr, {
								size: 19,
								className: "text-red-600"
							}), " Quá hạn và sắp tới hạn"]
						}), /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/viec-can-xu-ly",
							className: "text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
							children: ["Tất cả ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
						})]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "space-y-2.5",
						children: [c.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 py-3",
							children: "Không có việc tới hạn theo readiness hiện tại."
						}), c.map((e) => /* @__PURE__ */ (0, F.jsxs)(P, {
							to: e.route,
							className: "flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift",
							children: [
								/* @__PURE__ */ (0, F.jsx)("span", { className: B("w-2.5 h-10 rounded-full shrink-0", e.statusTone === "red" ? "bg-red-500" : e.statusTone === "amber" ? "bg-amber-500" : e.statusTone === "blue" ? "bg-blue-500" : "bg-slate-400") }),
								/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "flex-1 min-w-0",
									children: [/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block font-bold text-[14.5px] text-[#0f2a4a]",
										children: [
											e.lot,
											" · ",
											e.job
										]
									}), /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block text-[13px] text-slate-500",
										children: [
											V(e.due),
											" · ",
											V(e.dueNote)
										]
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "touch-target inline-flex items-center text-[13.5px] font-bold text-[#1e5aa8]",
									children: ["Xử lý ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
								})
							]
						}, e.id))]
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center justify-between mb-3",
							children: [/* @__PURE__ */ (0, F.jsx)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
								children: "Trạng thái các lô đang chạy"
							}), /* @__PURE__ */ (0, F.jsxs)(P, {
								to: "/lo-hang",
								className: "text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
								children: ["Tất cả lô ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "space-y-2.5",
							children: [l.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[14px] text-slate-500 py-3",
								children: "Không có lô nào đang chạy."
							}), l.map((t) => {
								let n = e.find((e) => e.id === t.id);
								return /* @__PURE__ */ (0, F.jsxs)(P, {
									to: t.to,
									className: "flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift",
									children: [
										/* @__PURE__ */ (0, F.jsx)(va, { tone: n?.statusTone ?? "gray" }),
										/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "flex-1 min-w-0",
											children: [/* @__PURE__ */ (0, F.jsxs)("span", {
												className: "block font-bold text-[14.5px] text-[#0f2a4a]",
												children: [
													t.id,
													" · ",
													t.customer
												]
											}), /* @__PURE__ */ (0, F.jsxs)("span", {
												className: "block text-[13px] text-slate-500 truncate",
												children: ["Tiếp theo: ", t.nextAction]
											})]
										}),
										/* @__PURE__ */ (0, F.jsx)(H, {
											tone: n?.statusTone ?? "gray",
											size: "sm",
											children: t.status
										})
									]
								}, t.id);
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl bg-blue-50 border border-blue-200 p-3 flex items-start gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(Nr, {
								size: 17,
								className: "text-blue-700 mt-0.5 shrink-0"
							}), /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13.5px] text-blue-900",
								children: [/* @__PURE__ */ (0, F.jsx)("b", { children: "Luồng gợi ý:" }), " Tổng quan → mở lô → xử lý việc tiếp theo → hợp đồng → xuất chứng từ → thu tiền."]
							})]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex items-center justify-between mb-3",
					children: [/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
						children: "Tiền hôm nay — hiện trạng → việc thiếu → hành động"
					}), /* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/tai-chinh/thu-tien",
						className: "text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
						children: ["Mở tài chính ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid grid-cols-1 md:grid-cols-3 gap-3",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-emerald-50 border border-emerald-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13px] font-semibold text-emerald-800",
									children: [
										"Còn phải thu · ",
										ma(t?.outstandingTotal),
										" ₫"
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13.5px] text-emerald-900 mt-1",
									children: [t?.outstandingCount ?? 0, " lô còn công nợ theo core.logic"]
								}),
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/tai-chinh/thu-tien",
									className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-[14.5px] px-4 min-h-[44px]",
									children: "GHI NHẬN THANH TOÁN"
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-amber-50 border border-amber-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13px] font-semibold text-amber-800",
									children: [
										"Cần đối soát · ",
										s?.financialAttention ?? 0,
										" lô"
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13.5px] text-amber-900 mt-1",
									children: "Quote Estimate ≠ Finance Actual — đối soát từng lô"
								}),
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/tai-chinh/doi-soat",
									className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-amber-500 text-white font-bold text-[14.5px] px-4 min-h-[44px]",
									children: "ĐỐI SOÁT NGAY"
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-blue-50 border border-blue-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13px] font-semibold text-blue-800",
									children: ["Hồ sơ thiếu thông tin · ", t?.missingDocsTotal ?? 0]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13.5px] text-blue-900 mt-1",
									children: [s?.missingInfo ?? 0, " lô thiếu dữ liệu bắt buộc"]
								}),
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/viec-can-xu-ly",
									className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px]",
									children: "MỞ DANH SÁCH VIỆC"
								})
							]
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/Tasks.tsx
var ja = {
	Khan: {
		label: "Khẩn",
		cls: "bg-red-600 text-white"
	},
	CanXuLy: {
		label: "Cần xử lý",
		cls: "bg-amber-400 text-amber-950"
	},
	BinhThuong: {
		label: "Bình thường",
		cls: "bg-slate-200 text-slate-700"
	}
};
function Ma() {
	let [e, t] = (0, _.useState)("ALL"), [n, r] = (0, _.useState)(""), i = (0, _.useMemo)(() => sa.filter((t) => (e === "ALL" || t.level === e) && (!n || (t.lot + t.customer + t.job + t.assignee).toLowerCase().includes(n.toLowerCase()))), [e, n]), a = (0, _.useMemo)(() => ({
		ALL: sa.length,
		Khan: sa.filter((e) => e.level === "Khan").length,
		CanXuLy: sa.filter((e) => e.level === "CanXuLy").length,
		BinhThuong: sa.filter((e) => e.level === "BinhThuong").length
	}), [sa.length, sa]);
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [/* @__PURE__ */ (0, F.jsx)(ya, {
					title: "Việc Cần Xử Lý",
					sub: "Hiện trạng → việc thiếu → bấm XỬ LÝ NGAY để tới đúng ô cần nhập. Làm mục Khẩn trước 17:00."
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex flex-col md:flex-row gap-2.5",
					children: [/* @__PURE__ */ (0, F.jsx)("input", {
						value: n,
						onChange: (e) => r(e.target.value),
						placeholder: "Lọc theo mã lô, khách hàng, người phụ trách…",
						className: "flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none"
					}), /* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2 overflow-x-auto no-scrollbar",
						children: [
							"ALL",
							"Khan",
							"CanXuLy",
							"BinhThuong"
						].map((n) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => t(n),
							className: B("touch-target shrink-0 rounded-xl border-2 px-4 min-h-[48px] text-[14.5px] font-bold", e === n ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: n === "ALL" ? `Tất cả (${a.ALL})` : n === "Khan" ? `Khẩn (${a.Khan})` : n === "CanXuLy" ? `Cần xử lý (${a.CanXuLy})` : `Bình thường (${a.BinhThuong})`
						}, n))
					})]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14.5px] min-w-[980px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Ưu tiên" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Mã lô" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Việc cần làm" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Người phụ trách" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hạn" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: i.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("span", {
									className: B("inline-flex items-center gap-1.5 text-[12.5px] font-extrabold rounded-full px-2.5 py-1 whitespace-nowrap", ja[e.level].cls),
									children: ja[e.level].label
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-extrabold text-[#0f2a4a]",
									children: /* @__PURE__ */ (0, F.jsx)(P, {
										to: e.route,
										className: "hover:underline whitespace-nowrap",
										children: e.lot
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: e.customer }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "max-w-[260px]",
									children: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-semibold",
										children: e.job
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "whitespace-nowrap",
									children: e.assignee
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-bold text-red-700 whitespace-nowrap",
									children: e.due
								}), /* @__PURE__ */ (0, F.jsx)("span", {
									className: "block text-[12.5px] text-slate-500",
									children: e.dueNote
								})] }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)(P, {
									to: e.route,
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white text-[13.5px] font-bold px-3.5 min-h-[44px] whitespace-nowrap",
									children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
								}) })
							]
						}, e.id)) })]
					})
				}), i.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
					className: "p-8 text-center text-slate-500",
					children: ["Không có việc nào khớp. ", /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: () => {
							t("ALL"), r("");
						},
						className: "font-bold text-[#1e5aa8]",
						children: "Xóa lọc"
					})]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [i.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center gap-2 flex-wrap",
							children: [
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: B("inline-flex items-center text-[12px] font-extrabold rounded-full px-2.5 py-1", ja[e.level].cls),
									children: ja[e.level].label
								}),
								/* @__PURE__ */ (0, F.jsx)(H, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}),
								/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "ml-auto text-[12.5px] font-bold text-red-700",
									children: ["⏰ ", e.due]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "font-extrabold text-[16px] text-[#0f2a4a] mt-2",
							children: [
								e.lot,
								" · ",
								e.customer
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-1.5 rounded-xl bg-slate-50 border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
									children: "Việc cần làm"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[15px] font-semibold text-slate-800 mt-0.5",
									children: e.job
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13px] text-slate-500 mt-1",
									children: [
										"👤 ",
										e.assignee,
										" · ",
										e.dueNote
									]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)(P, {
							to: e.route,
							className: "btn-press touch-target mt-3 flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[15.5px] min-h-[52px]",
							children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 18 })]
						})
					]
				}, e.id)), i.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center text-slate-500",
					children: ["Không có việc nào. ", /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: () => {
							t("ALL"), r("");
						},
						className: "font-bold text-[#1e5aa8]",
						children: "Xóa lọc"
					})]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-4 flex items-start gap-3 text-[14px] text-slate-500",
				children: [/* @__PURE__ */ (0, F.jsx)(pi, {
					size: 19,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, F.jsxs)("p", { children: [
					"Mẹo cho người mới: xử lý theo thứ tự ",
					/* @__PURE__ */ (0, F.jsx)("b", { children: "Khẩn → Cần xử lý → Bình thường" }),
					". Mỗi dòng đều có nút XỬ LÝ NGAY dẫn tới đúng ô nhập liệu."
				] })]
			})
		]
	});
}
//#endregion
//#region src/pages/Shipments.tsx
function Na() {
	let { shipments: e } = Xn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)("ALL"), [a, o] = (0, _.useState)(!1), s = (0, _.useMemo)(() => e.filter((e) => (r === "ALL" || e.status === r) && (!t || (e.id + e.customer + e.contract + e.route + e.sale + e.support).toLowerCase().includes(t.toLowerCase()))), [
		e,
		t,
		r
	]), c = ["ALL", ...Array.from(new Set(e.map((e) => e.status)))];
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						title: "Lô Hàng",
						sub: "Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu",
						right: /* @__PURE__ */ (0, F.jsx)(P, {
							to: "/tao-lo-moi",
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: "＋ Tạo lô mới"
						})
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								placeholder: "Nhập mã lô (LO-0306), khách (An Phát), hợp đồng…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => o((e) => !e),
							className: B("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", a ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, F.jsx)(R, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					a && /* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: c.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => i(e),
							className: B("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", r === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : e
						}, e))
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [s.length, " lô"]
							}),
							t ? /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
								" cho “",
								t,
								"”"
							] }) : null,
							" · Mỗi lô hiển thị: hiện trạng → việc tiếp theo → nút xử lý."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: /* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[1080px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Mã lô" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hợp đồng · Tuyến" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Việc tiếp theo" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Sale · Support" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: s.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("td", { children: [/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/lo-hang/" + e.id,
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsxs)("span", {
									className: "block text-[12px] text-slate-400",
									children: ["Cập nhật ", e.updated]
								})] }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "max-w-[220px]",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[13px] font-semibold text-slate-600",
										children: e.contract
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[13px] text-slate-500",
										children: e.route
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "max-w-[240px]",
									children: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block font-semibold text-[13.5px]",
										children: e.nextAction
									})
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Sale: ", /* @__PURE__ */ (0, F.jsx)("b", { children: e.sale })]
									}), /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["SP: ", /* @__PURE__ */ (0, F.jsx)("b", { children: e.support })]
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, F.jsx)(P, {
										to: e.nextRoute,
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]",
										children: "XỬ LÝ"
									}), /* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/lo-hang/" + e.id,
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(qr, { size: 15 }), " 360°"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [s.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, F.jsx)(va, { tone: e.statusTone }),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: e.statusTone,
										size: "sm",
										children: e.status
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] text-slate-500",
								children: e.route
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "mt-2.5 rounded-xl bg-amber-50 border border-amber-200 p-3",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[11.5px] font-bold uppercase tracking-wide text-amber-700",
									children: "Việc tiếp theo"
								}), /* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[14px] font-semibold text-slate-800 mt-0.5",
									children: e.nextAction
								})]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-2",
								children: [
									"Sale ",
									e.sale,
									" · SP ",
									e.support,
									" · ",
									e.updated
								]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, F.jsxs)(P, {
							to: e.nextRoute,
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: ["XỬ LÝ ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
						}), /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/lo-hang/" + e.id,
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(qr, { size: 17 }), " XEM 360°"]
						})]
					})]
				}, e.id)), s.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy lô nào"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo lô mới."
						}),
						/* @__PURE__ */ (0, F.jsx)(P, {
							to: "/tao-lo-moi",
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
							children: "＋ Tạo lô mới"
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/ShipmentDetail.tsx
var Pa = [
	{
		id: "lay-hang",
		label: "Lấy hàng & Xuất khẩu",
		short: "Lấy hàng"
	},
	{
		id: "nhap",
		label: "Nhập khẩu & Giao hàng",
		short: "Nhập & Giao"
	},
	{
		id: "tai-chinh",
		label: "Tài chính / Công nợ",
		short: "Tài chính"
	},
	{
		id: "chung-tu",
		label: "Chứng từ & PXK",
		short: "Chứng từ"
	},
	{
		id: "lich-su",
		label: "Lịch sử",
		short: "Lịch sử"
	}
];
function Fa() {
	let { id: e } = Ct(), [t, n] = Bn(), r = t.get("tab") || "lay-hang", { shipments: i, updateShipment: a, toast: o, contracts: s, dispatch: c } = Xn(), l = xt(), u = i.find((t) => t.id === e), [d, f] = (0, _.useState)(!1), [p, m] = (0, _.useState)(!1), [h, g] = (0, _.useState)(""), [v, y] = (0, _.useState)("Thu tiền khách"), [b, x] = (0, _.useState)({
		name: "",
		qty: "1",
		price: "",
		cost: "",
		vat: "8"
	}), [S, C] = (0, _.useState)({}), [w, T] = (0, _.useState)(0);
	(0, _.useEffect)(() => {
		C({}), x({
			name: "",
			qty: "1",
			price: "",
			cost: "",
			vat: "8"
		});
	}, [e, r]);
	let E = (e, t) => C((n) => ({
		...n,
		[e]: t
	})), D = (e, t) => S[e] ?? t, O = (0, _.useMemo)(() => s.find((e) => e.id === u?.contract), [s, u]);
	if (!u) return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "font-extrabold text-[19px]",
				children: ["Không tìm thấy lô ", e]
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "text-slate-500 mt-1 text-[15px]",
				children: "Mã lô có thể sai. Về danh sách để tìm lại."
			}),
			/* @__PURE__ */ (0, F.jsx)(P, {
				to: "/lo-hang",
				className: "btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center",
				children: "Về danh sách lô"
			})
		]
	});
	let k = u.finance.currency || "VND", ee = (e) => {
		let t = {};
		for (let [n, r] of Object.entries(e)) {
			let e = (r ?? "").trim();
			e.length > 0 && (t[n] = e);
		}
		return t;
	}, te = (e) => {
		C({}), T(Date.now()), o(e, "Đã gửi tới backend. Dữ liệu sẽ được đọc lại từ Logistics sau khi ghi.", "green");
	}, ne = () => {
		let e = ee({
			container_no: D("plate", u.pickup.plate),
			etd: D("pickupTime", u.pickup.pickupTime),
			booking_no: D("bookingNo", u.transport?.bookingNo ?? ""),
			carrier: D("carrier", u.transport?.carrier ?? ""),
			pol: D("pol", u.transport?.pol ?? ""),
			pod: D("pod", u.transport?.pod ?? ""),
			qty_pkg: D("qtyPkg", u.transport?.qtyPkg ?? "")
		});
		if (Object.keys(e).length === 0) {
			o("Chưa có gì để lưu", "Nhập ít nhất một trường ở tab Lấy hàng & Xuất khẩu.", "red");
			return;
		}
		c("shipment_field_save", {
			shipmentId: u.id,
			fields: e
		}), te("Đã lưu thông tin lấy hàng " + u.id);
	}, re = () => {
		let e = D("tk", u.importInfo.declarationNo);
		if (!e) {
			o("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red");
			return;
		}
		let t = {
			tk_no: e,
			...ee({
				phan_luong: D("inspection", u.importInfo.inspection),
				arrival_date: D("arrivalDate", u.importInfo.arrivalDate ?? ""),
				free_time: D("freeTime", u.importInfo.freeTime == null ? "" : String(u.importInfo.freeTime)),
				truck_no: D("plateVN", u.importInfo.plateVN),
				seal_no: D("driverVN", u.importInfo.driverVN)
			})
		};
		c("shipment_field_save", {
			shipmentId: u.id,
			fields: t
		}), te("Đã lưu tờ khai " + e);
	}, ie = () => {
		let e = c("delivery_confirm", {
			shipmentId: u.id,
			deliveredAt: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			receiverName: u.importInfo.receiver,
			receiverTitle: u.importInfo.receiverTitle ?? "",
			receiverPhone: u.importInfo.receiverPhone,
			deliveryLocation: u.importInfo.deliveryLocation || u.importInfo.deliveryAddr
		});
		m(!1), e ? o("Đã gửi xác nhận giao hàng " + u.id, "Backend ghi nhận + audit; PXK sẽ mở ở tab Chứng từ.", "green") : o("Không gửi được", "Component chưa kết nối backend.", "red");
	}, A = (0, _.useRef)(""), j = () => {
		A.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, f(!0);
	}, M = () => {
		let e = Number(h.replace(/\D/g, ""));
		if (!e) {
			o("Chưa nhập số tiền", `Nhập số tiền ${k} rồi bấm Lưu — ví dụ 50.000.000.`, "red");
			return;
		}
		if (!c("payment_record", {
			shipmentId: u.id,
			amount: e,
			requestId: A.current,
			date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			note: v
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		f(!1), g(""), o("Đã gửi khoản thu " + da(e, k), "Ghi qua save_direct_shipment_payment với request identity — gửi lại cùng intent sẽ không nhân đôi.", "green");
	}, ae = (e, t) => x((n) => ({
		...n,
		[e]: t
	})), oe = () => {
		if (!b.name.trim()) {
			o("Thiếu tên dịch vụ", "Nhập tên dòng thực tế — ví dụ: Cước xe TQ.", "red");
			return;
		}
		if (!c("finance_actual_save", {
			shipmentId: u.id,
			line: {
				name: b.name.trim(),
				qty: b.qty,
				price: b.price,
				cost: b.cost,
				vat: b.vat
			}
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		o("Đã gửi dòng thực tế", "Ghi vào data['3.4'].details rồi core.logic tính lại phải thu / chi phí / lợi nhuận.", "green"), x({
			name: "",
			qty: "1",
			price: "",
			cost: "",
			vat: "8"
		});
	}, se = () => {
		c("pxk_generate", { shipmentId: u.id }) ? o("Đã gửi yêu cầu xuất PXK", "core.docgen kiểm tra gate giao hàng rồi sinh file Office thật.", "blue") : o("Không gửi được", "Component chưa kết nối backend.", "red");
	}, ce = (e) => /tờ khai|thông quan|xe giao|giao hàng/i.test(e) ? "nhap" : /lấy hàng|xe TQ|biển số|packing|container/i.test(e) ? "lay-hang" : /chứng từ|PXK|HDMB|PL$/i.test(e) ? "chung-tu" : "nhap", le = u.missingDocs.length;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("button", {
				onClick: () => l(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, F.jsx)(pr, { size: 17 }), " Quay lại"]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [
					/* @__PURE__ */ (0, F.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4 md:p-6",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap items-center gap-2",
								children: [
									/* @__PURE__ */ (0, F.jsx)("h1", {
										className: "text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]",
										children: u.id
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: u.statusTone,
										children: u.status
									}),
									le > 0 && /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "inline-flex items-center gap-1.5 text-[13px] font-bold bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1.5",
										children: [
											/* @__PURE__ */ (0, F.jsx)(Nr, { size: 15 }),
											" Thiếu ",
											le,
											" thông tin"
										]
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "ml-auto text-[12.5px] text-slate-400 flex items-center gap-1",
										children: [
											/* @__PURE__ */ (0, F.jsx)(zr, { size: 14 }),
											" Cập nhật ",
											u.updated
										]
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-semibold text-[15.5px] mt-1",
								children: [
									u.customer,
									" ",
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "text-slate-400 font-normal",
										children: ["· MST ", u.customerMST]
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-2 md:grid-cols-4 gap-x-6 mt-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Tuyến",
										value: u.route
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Cửa khẩu",
										value: u.borderVN
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Hợp đồng",
										value: /* @__PURE__ */ (0, F.jsx)(P, {
											to: "/hop-dong/" + u.contract,
											className: "text-[#1e5aa8] font-bold hover:underline",
											children: u.contract
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Sale · Support",
										value: /* @__PURE__ */ (0, F.jsxs)("span", { children: [
											u.sale,
											" · ",
											u.support
										] })
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "px-4 md:px-6 pb-4 md:pb-5",
						children: /* @__PURE__ */ (0, F.jsx)(Ca, {
							tone: u.statusTone === "green" ? "green" : u.priority === "Khan" ? "red" : "amber",
							title: u.nextAction,
							desc: u.nextActionDetail,
							action: u.nextLabel,
							onAction: () => {
								if (t.get("tab"), u.nextRoute.startsWith("/lo-hang")) {
									let e = u.nextRoute.match(/tab=(\w+)/);
									n(e ? { tab: e[1] } : {}), document.getElementById("workspace-tabs")?.scrollIntoView({ behavior: "smooth" });
								} else l(u.nextRoute);
							}
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						id: "workspace-tabs",
						className: "px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3",
						children: Pa.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => n({ tab: e.id }),
							className: B("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", r === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: "hidden md:inline",
								children: e.label
							}), /* @__PURE__ */ (0, F.jsx)("span", {
								className: "md:hidden",
								children: e.short
							})]
						}, e.id))
					})
				]
			}),
			u.missingDocs.length > 0 && r !== "chung-tu" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-red-200 p-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("p", {
					className: "font-extrabold text-[15px] text-red-800 flex items-center gap-2 mb-2.5",
					children: [
						/* @__PURE__ */ (0, F.jsx)(Nr, { size: 18 }),
						" Đang thiếu ",
						u.missingDocs.length,
						" thông tin — bấm để bổ sung ngay:"
					]
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "grid gap-2 md:grid-cols-2",
					children: u.missingDocs.map((e) => /* @__PURE__ */ (0, F.jsx)(wa, {
						what: e,
						actionLabel: "Bổ sung ngay",
						onAction: () => {
							n({ tab: ce(e) }), setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({
								behavior: "smooth",
								block: "center"
							}), 150);
						}
					}, e))
				})]
			}),
			r === "lay-hang" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				id: "missing-anchor",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(hi, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Nhà máy & lịch lấy hàng"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3.5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-bold text-[15px]",
									children: u.pickup.factory
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13.5px] text-slate-500",
									children: u.pickup.address
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] mt-1.5 flex items-center gap-1.5",
									children: [
										/* @__PURE__ */ (0, F.jsx)(Di, {
											size: 15,
											className: "text-slate-400"
										}),
										" ",
										u.pickup.contact,
										" · ",
										u.pickup.phone
									]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Thời gian lấy hàng",
								required: !u.pickup.pickupTime,
								error: D("pickupTime", u.pickup.pickupTime) ? void 0 : "Thiếu giờ lấy — nhà máy cần báo trước 24h",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: D("pickupTime", u.pickup.pickupTime),
									onChange: (e) => E("pickupTime", e.target.value),
									placeholder: "VD: 10/09/2026 09:00",
									className: W(D("pickupTime", u.pickup.pickupTime) ? "ok" : "missing")
								})
							}), /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Loại / kích thước xe",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									defaultValue: u.pickup.truckType,
									className: W()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 pt-1",
							children: [/* @__PURE__ */ (0, F.jsx)(Gi, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Xe Trung Quốc"]
						}),
						(!u.pickup.plate || !u.pickup.driver) && /* @__PURE__ */ (0, F.jsx)(wa, {
							what: "biển số + tài xế xe TQ",
							where: "Chưa đặt được xe — bổ sung để nhà máy cho hàng lên xe",
							actionLabel: "Nhập xe ngay",
							onAction: () => document.getElementById("fld-plate")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Biển số xe",
									required: !u.pickup.plate,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-plate",
										value: D("plate", u.pickup.plate),
										onChange: (e) => E("plate", e.target.value),
										placeholder: "VD: 粤A·88T36",
										className: W(D("plate", u.pickup.plate) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Tài xế",
									required: !u.pickup.driver,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: D("driver", u.pickup.driver),
										onChange: (e) => E("driver", e.target.value),
										placeholder: "Tên tài xế",
										className: W(D("driver", u.pickup.driver) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "SĐT tài xế",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: D("driverPhone", u.pickup.driverPhone),
										onChange: (e) => E("driverPhone", e.target.value),
										placeholder: "+86…",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-2 gap-3",
									children: [/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Ngày dự kiến",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											defaultValue: u.pickup.eta,
											className: W()
										})
									}), /* @__PURE__ */ (0, F.jsx)(U, {
										label: "Ngày thực tế",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											defaultValue: u.pickup.ata,
											placeholder: "—",
											className: W()
										})
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(ba, {
							onClick: ne,
							className: "w-full",
							children: "💾 LƯU THÔNG TIN LẤY HÀNG"
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "space-y-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3",
									children: [/* @__PURE__ */ (0, F.jsx)(Ci, {
										size: 19,
										className: "text-[#1e5aa8]"
									}), " Hàng hóa"]
								}),
								/* @__PURE__ */ (0, F.jsx)("div", {
									className: "grid grid-cols-2 md:grid-cols-3 gap-3",
									children: [
										["Số kiện / GW", V(u.cargo.qtyPkg)],
										["Số kiện", ha(u.cargo.packs)],
										["CBM", ha(u.cargo.cbm)],
										["Kích thước", V(u.cargo.dims)],
										["Loại hàng", V(u.cargo.type)]
									].map(([e, t]) => /* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-slate-50 border border-slate-200 p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
											children: e
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-bold text-[15px] text-[#0f2a4a] mt-0.5",
											children: t
										})]
									}, e))
								}),
								u.cargo.note && /* @__PURE__ */ (0, F.jsxs)("p", {
									className: "mt-2.5 text-[13.5px] bg-amber-50 border border-amber-200 rounded-xl p-3",
									children: ["📌 Ghi chú: ", u.cargo.note]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
									children: ["Xuất khẩu — ", u.exportInfo.border]
								}),
								/* @__PURE__ */ (0, F.jsx)(Ta, {
									label: "Đơn vị khai",
									value: u.exportInfo.declarant
								}),
								/* @__PURE__ */ (0, F.jsx)(Ta, {
									label: "Ngày dự kiến / thực tế",
									value: /* @__PURE__ */ (0, F.jsxs)("span", { children: [
										u.exportInfo.eta || "—",
										" / ",
										u.exportInfo.ata || "chưa có"
									] })
								}),
								/* @__PURE__ */ (0, F.jsx)(Ta, {
									label: "Trạng thái",
									value: /* @__PURE__ */ (0, F.jsx)(H, {
										tone: u.exportInfo.state.includes("Đã") ? "green" : "amber",
										size: "sm",
										children: u.exportInfo.state
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-1",
									children: "Checklist chứng từ xuất khẩu"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] text-slate-500 mb-3",
									children: "Hiện trạng → thiếu gì → bấm để bổ sung. Không có cảnh báo cụt."
								}),
								/* @__PURE__ */ (0, F.jsx)("div", {
									className: "space-y-2",
									children: u.docs.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
										className: B("flex items-center gap-3 rounded-xl border-2 p-3", e.ok ? "border-emerald-200 bg-emerald-50/60" : "border-amber-300 bg-amber-50"),
										children: [
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: B("w-8 h-8 rounded-full grid place-items-center font-extrabold shrink-0", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
												children: e.ok ? "✓" : "!"
											}),
											/* @__PURE__ */ (0, F.jsxs)("div", {
												className: "flex-1 min-w-0",
												children: [/* @__PURE__ */ (0, F.jsxs)("p", {
													className: "font-bold text-[14.5px]",
													children: [
														e.name,
														" — ",
														e.ok ? /* @__PURE__ */ (0, F.jsx)("span", {
															className: "text-emerald-700",
															children: "✅ Đủ"
														}) : /* @__PURE__ */ (0, F.jsx)("span", {
															className: "text-amber-800",
															children: "Thiếu"
														})
													]
												}), e.note && /* @__PURE__ */ (0, F.jsx)("p", {
													className: "text-[13px] text-slate-600",
													children: e.note
												})]
											}),
											!e.ok && /* @__PURE__ */ (0, F.jsxs)("button", {
												onClick: () => {
													n({ tab: "chung-tu" }), o("Mở tab Chứng từ", "Tải file " + e.name + " lên hoặc ghi chú lý do thiếu.", "blue");
												},
												className: "btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13.5px] font-bold px-3 min-h-[44px]",
												children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 14 }), " Bổ sung"]
											})
										]
									}, e.name))
								})
							]
						})
					]
				})]
			}),
			r === "nhap" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				id: "missing-anchor",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
							children: ["Tờ khai & thuế nhập khẩu — ", u.importInfo.borderVN]
						}),
						!D("tk", u.importInfo.declarationNo) && /* @__PURE__ */ (0, F.jsx)(wa, {
							what: "số tờ khai nhập khẩu",
							where: "Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được",
							actionLabel: "Nhập số TK",
							onAction: () => document.getElementById("fld-tk")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Số tờ khai",
									required: !u.importInfo.declarationNo,
									error: D("tk", u.importInfo.declarationNo) ? void 0 : "Nhập 12 số tờ khai — VD: 105588421330",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-tk",
										value: D("tk", u.importInfo.declarationNo),
										onChange: (e) => E("tk", e.target.value),
										placeholder: "12 số tờ khai…",
										className: W(D("tk", u.importInfo.declarationNo) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Ngày đăng ký",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: D("regDate", u.importInfo.regDate),
										onChange: (e) => E("regDate", e.target.value),
										placeholder: "VD: 09/09/2026",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Thuế nhập khẩu (VND)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.importInfo.tax == null ? "" : String(u.importInfo.tax),
										readOnly: !0,
										placeholder: "Chưa có dữ liệu — theo dõi ở GNT",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "VAT hàng nhập (VND)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.importInfo.vat == null ? "" : String(u.importInfo.vat),
										readOnly: !0,
										placeholder: "Chưa có dữ liệu — theo dõi ở GNT",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Phân luồng / kiểm hóa",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: D("inspection", u.importInfo.inspection),
										onChange: (e) => E("inspection", e.target.value),
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Giấy phép chuyên ngành",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.importInfo.license,
										className: W()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(ba, {
							onClick: re,
							className: "w-full",
							children: "💾 LƯU TỜ KHAI & THUẾ"
						}),
						D("tk", u.importInfo.declarationNo) && /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13.5px] text-blue-900",
							children: [
								"✅ Đã có số TK ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: D("tk", u.importInfo.declarationNo) }),
								". Tiếp theo: nộp thuế rồi bấm “Thông quan” khi có kết quả phân luồng."
							]
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(Gi, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Xe Việt Nam & giao hàng"]
						}),
						(!u.importInfo.driverVN || !u.importInfo.plateVN) && !u.importInfo.delivered && /* @__PURE__ */ (0, F.jsx)(wa, {
							what: "xe VN + tài xế",
							where: "Chưa đặt xe — đặt trước giờ giao ít nhất 4 tiếng",
							actionLabel: "Đặt xe ngay",
							onAction: () => document.getElementById("fld-platevn")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Loại xe VN",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.importInfo.truckVN,
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Biển số VN",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-platevn",
										value: D("plateVN", u.importInfo.plateVN),
										onChange: (e) => E("plateVN", e.target.value),
										placeholder: "VD: 29H-481.36",
										className: W(D("plateVN", u.importInfo.plateVN) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Tài xế VN",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: D("driverVN", u.importInfo.driverVN),
										onChange: (e) => E("driverVN", e.target.value),
										placeholder: "Tên tài xế",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Lịch giao",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.importInfo.schedule,
										className: W()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3.5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12.5px] font-bold uppercase tracking-wide text-slate-400",
									children: "Địa chỉ giao"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-bold text-[15px] mt-0.5",
									children: u.importInfo.deliveryAddr
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-slate-600 mt-1",
									children: [
										"Người nhận: ",
										/* @__PURE__ */ (0, F.jsx)("b", { children: u.importInfo.receiver }),
										" · ",
										u.importInfo.receiverPhone
									]
								}),
								u.importInfo.actualDelivery && /* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-emerald-700 font-bold mt-1",
									children: ["✅ Đã giao: ", u.importInfo.actualDelivery]
								})
							]
						}),
						u.importInfo.delivered ? /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-extrabold text-[17px] text-emerald-800",
									children: "✅ ĐÃ GIAO HÀNG XONG"
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13.5px] text-emerald-700",
									children: [u.importInfo.actualDelivery, " · Sang tab Chứng từ để xuất PXK →"]
								}),
								/* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => n({ tab: "chung-tu" }),
									className: "btn-press touch-target mt-2.5 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]",
									children: ["SANG XUẤT PHIẾU XUẤT KHO ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
								})
							]
						}) : /* @__PURE__ */ (0, F.jsx)(xa, {
							onClick: () => m(!0),
							className: "w-full text-[17px] min-h-[56px]",
							children: "✅ XÁC NHẬN ĐÃ GIAO HÀNG"
						})
					]
				})]
			}),
			r === "tai-chinh" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "space-y-4",
				id: "missing-anchor",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
						children: [/* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border-2 border-dashed border-violet-300 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-violet-600 bg-violet-100 inline-block rounded-md px-2 py-0.5",
									children: "Báo giá / Dự kiến — chưa phải số thực thu/chi"
								}),
								/* @__PURE__ */ (0, F.jsx)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2",
									children: "Chi phí dự kiến theo báo giá"
								}),
								u.finance.quote.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-slate-500",
									children: ["Chưa gắn báo giá. ", /* @__PURE__ */ (0, F.jsx)(P, {
										to: "/kinh-doanh-bao-gia",
										className: "font-bold text-[#1e5aa8]",
										children: "Mở báo giá →"
									})]
								}),
								u.finance.quote.map((e) => /* @__PURE__ */ (0, F.jsx)(Ta, {
									label: e.label,
									value: /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "font-bold text-[16px]",
										children: [
											la(e.amount, e.ccy),
											" ",
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[12px] font-bold text-violet-600",
												children: e.ccy
											})
										]
									})
								}, e.label)),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung."
								})
							]
						}), /* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-emerald-700 bg-emerald-100 inline-block rounded-md px-2 py-0.5",
									children: "Thực tế — đã phát sinh, có chứng từ"
								}),
								/* @__PURE__ */ (0, F.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2",
									children: [
										"Doanh thu & chi phí thực tế (",
										k,
										")"
									]
								}),
								u.finance.actual.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-slate-500",
									children: [
										"Chưa ghi nhận dòng thực tế nào — doanh thu / chi phí / lợi nhuận thực tế đang ",
										/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
										", không phải 0."
									]
								}),
								u.finance.actual.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "py-2 border-b border-slate-100 last:border-0",
									children: [/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "flex items-start justify-between gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "text-[13.5px] text-slate-500 font-medium pt-0.5",
											children: e.label
										}), /* @__PURE__ */ (0, F.jsx)("span", {
											className: "text-right font-semibold text-slate-800 text-[14.5px]",
											children: /* @__PURE__ */ (0, F.jsx)("span", {
												className: "font-bold text-[16px]",
												children: da(e.amount, e.ccy)
											})
										})]
									}), /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-400 mt-0.5 text-right",
										children: [
											"Chi phí ",
											da(e.cost, e.ccy),
											e.qty == null ? "" : ` · SL ${ha(e.qty)}`,
											e.vat == null ? "" : ` · VAT ${ha(e.vat)}%`
										]
									})]
								}, `${e.label}-${t}`)),
								/* @__PURE__ */ (0, F.jsx)(Ta, {
									label: "Doanh thu thực tế (chưa VAT)",
									value: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-bold",
										children: da(u.finance.receivableNet, k)
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(Ta, {
									label: "Chi phí thực tế",
									value: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-bold",
										children: da(u.finance.payable, k)
									})
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3",
									children: [
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] font-extrabold uppercase tracking-wider text-emerald-700",
											children: "Lợi nhuận thực tế"
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "grid grid-cols-2 gap-2 mt-1.5 text-center",
											children: [/* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Lãi / Lỗ thực tế"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: B("font-extrabold text-[17px]", u.finance.profit == null ? "text-slate-400" : u.finance.profit < 0 ? "text-red-700" : "text-emerald-700"),
												children: da(u.finance.profit, k)
											})] }), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Biên lợi nhuận"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: B("font-extrabold text-[17px]", u.finance.profitMargin == null ? "text-slate-400" : u.finance.profitMargin < 0 ? "text-red-700" : "text-emerald-700"),
												children: pa(u.finance.profitMargin)
											})] })]
										}),
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12.5px] text-slate-500 mt-2",
											children: "= Doanh thu thực tế − chi phí thực tế − hoa hồng. Không gồm VAT đầu ra. Không lấy số báo giá để bù chỗ trống."
										})
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3 rounded-xl border border-slate-200 p-3",
									children: [
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[13px] font-extrabold text-[#0f2a4a] mb-2",
											children: "Ghi nhận dòng thực tế"
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "grid gap-2.5",
											children: [
												/* @__PURE__ */ (0, F.jsx)(U, {
													label: "Dịch vụ",
													required: !0,
													error: b.name.trim() ? void 0 : "Nhập tên dịch vụ",
													children: /* @__PURE__ */ (0, F.jsx)("input", {
														value: b.name,
														onChange: (e) => ae("name", e.target.value),
														placeholder: "VD: Cước xe TQ Đông Bằng → Hữu Nghị",
														className: W(b.name.trim() ? "ok" : "missing")
													})
												}),
												/* @__PURE__ */ (0, F.jsxs)("div", {
													className: "grid grid-cols-2 gap-2.5",
													children: [/* @__PURE__ */ (0, F.jsx)(U, {
														label: `Giá bán (${k})`,
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: b.price,
															onChange: (e) => ae("price", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 62000000",
															className: W()
														})
													}), /* @__PURE__ */ (0, F.jsx)(U, {
														label: `Chi phí (${k})`,
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: b.cost,
															onChange: (e) => ae("cost", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 57000000",
															className: W()
														})
													})]
												}),
												/* @__PURE__ */ (0, F.jsxs)("div", {
													className: "grid grid-cols-2 gap-2.5",
													children: [/* @__PURE__ */ (0, F.jsx)(U, {
														label: "Số lượng",
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: b.qty,
															onChange: (e) => ae("qty", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 1",
															className: W()
														})
													}), /* @__PURE__ */ (0, F.jsx)(U, {
														label: "VAT %",
														hint: "Bỏ trống = chưa xác định",
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: b.vat,
															onChange: (e) => ae("vat", e.target.value),
															inputMode: "decimal",
															placeholder: "VD: 8",
															className: W()
														})
													})]
												})
											]
										}),
										/* @__PURE__ */ (0, F.jsx)(ba, {
											onClick: oe,
											className: "mt-3 w-full",
											children: "💾 LƯU DÒNG THỰC TẾ"
										})
									]
								})
							]
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-1 md:grid-cols-2 gap-4",
						children: [/* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-2",
									children: [
										/* @__PURE__ */ (0, F.jsx)(Zi, {
											size: 19,
											className: "text-emerald-600"
										}),
										" Phải thu khách hàng (",
										k,
										")"
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-3 gap-2 text-center",
									children: [
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Phải thu"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px]",
												children: fa(u.finance.receivable, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-emerald-700 font-semibold",
												children: "Đã thu"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-emerald-700",
												children: fa(u.finance.received, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-red-50 border border-red-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-red-600 font-semibold",
												children: "Còn phải thu"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-red-700",
												children: fa(u.finance.outstanding, k)
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Phải thu = doanh thu thực tế + VAT đầu ra. Còn phải thu = phải thu − đã thu, do backend tính."
								}),
								/* @__PURE__ */ (0, F.jsx)("button", {
									onClick: j,
									className: "btn-press touch-target mt-3 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
									children: "＋ GHI NHẬN THANH TOÁN"
								})
							]
						}), /* @__PURE__ */ (0, F.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-2",
									children: [
										"Phải trả đối tác (",
										k,
										")"
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-3 gap-2 text-center",
									children: [
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Phải trả"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px]",
												children: fa(u.finance.payable, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-blue-700 font-semibold",
												children: "Đã trả"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-blue-700",
												children: fa(u.finance.paid, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-amber-50 border border-amber-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-amber-700 font-semibold",
												children: "Còn phải trả"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-amber-800",
												children: fa(u.finance.paid == null ? null : (u.finance.payable ?? 0) - u.finance.paid, k)
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Phải trả là chi phí đã phát sinh. Tiền đã trả đối tác chưa có sổ theo dõi trên lô nên để “—”, không suy ra 0."
								}),
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/tai-chinh/doi-soat",
									className: "btn-press touch-target mt-3 w-full rounded-xl border-2 border-slate-200 font-bold min-h-[52px] flex items-center justify-center",
									children: "MỞ ĐỐI SOÁT"
								})
							]
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
							children: "Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa"
						}), /* @__PURE__ */ (0, F.jsx)("div", {
							className: "space-y-2",
							children: u.finance.payments.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "text-[12.5px] font-bold text-slate-400 w-[92px]",
										children: e.date
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "flex-1 min-w-[160px]",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "block font-bold text-[14.5px]",
											children: e.kind
										}), /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: [e.by, e.note ? " · " + e.note : ""]
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "font-extrabold text-[15.5px]",
										children: [
											la(e.amount, e.ccy),
											" ",
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[11.5px] text-slate-400",
												children: e.ccy
											})
										]
									}),
									/* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => o("Tạo bút toán điều chỉnh", "Nhập số điều chỉnh (+/-) thay vì xóa — giữ nguyên lịch sử kiểm toán.", "blue"),
										className: "touch-target text-[13px] font-bold text-[#1e5aa8] border border-slate-200 rounded-lg px-3 min-h-[40px]",
										children: "Điều chỉnh"
									})
								]
							}, t))
						})]
					})
				]
			}),
			r === "chung-tu" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3",
							children: [/* @__PURE__ */ (0, F.jsx)(ti, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Hợp đồng liên kết"]
						}),
						O ? /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl border-2 border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex flex-wrap items-center gap-2",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: O.id
									}), /* @__PURE__ */ (0, F.jsx)(H, {
										tone: O.statusTone,
										size: "sm",
										children: O.status
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-slate-600 mt-1",
									children: [
										O.companyLegal,
										" · Giá trị ",
										ua(O.value ?? u.finance.receivable)
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-2 gap-2 mt-3",
									children: [/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/hop-dong/" + O.id,
										className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]",
										children: [/* @__PURE__ */ (0, F.jsx)(qr, { size: 16 }), " MỞ HỢP ĐỒNG"]
									}), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => {
											n({ tab: "chung-tu" }), o("Chứng từ " + O.id, "Chứng từ được sinh bởi core.docgen (Office thật) ở tab Chứng từ & PXK.", "blue");
										},
										className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Zr, { size: 16 }), " MỞ CHỨNG TỪ"]
									})]
								})
							]
						}) : /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-slate-500 text-[14px]",
							children: ["Lô chưa gắn hợp đồng. ", /* @__PURE__ */ (0, F.jsx)(P, {
								to: "/hop-dong",
								className: "font-bold text-[#1e5aa8]",
								children: "Chọn hợp đồng →"
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)("h4", {
								className: "font-bold text-[14.5px] mb-2",
								children: "Chứng từ lô hàng — bấm để tải / bổ sung"
							}), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "space-y-2",
								children: u.docs.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5",
									children: [
										/* @__PURE__ */ (0, F.jsx)("span", {
											className: B("w-7 h-7 rounded-full grid place-items-center text-[13px] font-extrabold", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
											children: e.ok ? "✓" : "!"
										}),
										/* @__PURE__ */ (0, F.jsx)("span", {
											className: "flex-1 font-semibold text-[14px]",
											children: e.name
										}),
										e.ok ? /* @__PURE__ */ (0, F.jsxs)("button", {
											onClick: () => o("Đã tải " + e.name, "File minh họa của " + u.id + " đã lưu về máy.", "green"),
											className: "touch-target inline-flex items-center gap-1 text-[13px] font-bold text-[#1e5aa8] border rounded-lg px-2.5 min-h-[40px]",
											children: [/* @__PURE__ */ (0, F.jsx)(Ur, { size: 14 }), " Tải"]
										}) : /* @__PURE__ */ (0, F.jsx)("button", {
											onClick: () => o("Tải lên " + e.name, "Chọn file PDF/ảnh từ máy — prototype mô phỏng thao tác.", "blue"),
											className: "touch-target inline-flex items-center gap-1 text-[13px] font-bold text-white bg-amber-500 rounded-lg px-2.5 min-h-[40px]",
											children: "＋ Bổ sung"
										})
									]
								}, e.name))
							})]
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-1",
							children: "Phiếu xuất kho (PXK) — theo từng lô"
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[13px] text-slate-500 mb-3",
							children: [
								"PXK gắn với lô đã giao, nguồn từ ",
								u.pxk.source || u.contract,
								". Mỗi lô 1 PXK riêng."
							]
						}),
						!u.importInfo.delivered && /* @__PURE__ */ (0, F.jsx)(wa, {
							what: "xác nhận đã giao hàng",
							where: "Phải giao xong mới được xuất PXK",
							actionLabel: "Sang xác nhận giao",
							onAction: () => n({ tab: "nhap" })
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Số PXK",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.number,
										placeholder: "Tự sinh khi xuất",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Ngày PXK",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.date || "09/09/2026",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Địa điểm nhận",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.place || u.importInfo.deliveryAddr,
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Người nhận",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.receiver || u.importInfo.receiver,
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Chức vụ người nhận",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.role || "Thủ kho",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Nguồn (HDMB/PL)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										defaultValue: u.pxk.source || u.contract,
										className: W()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl bg-slate-50 border p-3 text-[13.5px]",
							children: [/* @__PURE__ */ (0, F.jsxs)("p", { children: ["Đã giao hàng xong: ", /* @__PURE__ */ (0, F.jsx)("b", {
								className: u.importInfo.delivered ? "text-emerald-700" : "text-red-600",
								children: u.importInfo.delivered ? "✅ Rồi — " + u.importInfo.actualDelivery : "❌ Chưa"
							})] }), /* @__PURE__ */ (0, F.jsxs)("p", { children: ["Ngày giao: ", /* @__PURE__ */ (0, F.jsx)("b", { children: u.importInfo.actualDelivery || u.importInfo.schedule })] })]
						}),
						u.pxk.done ? /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center",
							children: [/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-emerald-800",
								children: ["✅ ĐÃ XUẤT ", u.pxk.number]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: se,
								className: "btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(Ur, { size: 17 }), " TẢI LẠI PXK"]
							})]
						}) : /* @__PURE__ */ (0, F.jsx)(xa, {
							onClick: se,
							className: "w-full mt-3 text-[16px] min-h-[56px]",
							children: "🖨 XUẤT PHIẾU XUẤT KHO"
						})
					]
				})]
			}),
			r === "lich-su" && /* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 max-w-[800px]",
				children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
					className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-4",
					children: ["Dòng thời gian — ", u.id]
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200",
					children: u.timeline.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "relative",
						children: [
							/* @__PURE__ */ (0, F.jsx)("span", { className: B("absolute -left-6 top-1 w-4 h-4 rounded-full border-[3px] border-white shadow", e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : e.tone === "red" ? "bg-red-500" : "bg-blue-500") }),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12.5px] font-bold text-slate-400",
								children: e.time
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-bold text-[15px] text-[#0f2a4a]",
								children: e.title
							}),
							e.desc && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13.5px] text-slate-600",
								children: e.desc
							})
						]
					}, t))
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "xl:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: [
					r === "nhap" && !u.importInfo.delivered && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: () => m(!0),
						className: "btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
						children: "✅ XÁC NHẬN ĐÃ GIAO"
					}),
					r === "chung-tu" && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: se,
						className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]",
						children: "🖨 XUẤT PHIẾU XUẤT KHO"
					}),
					r === "tai-chinh" && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: j,
						className: "btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
						children: "＋ GHI NHẬN THANH TOÁN"
					}),
					(r === "lay-hang" || r === "lich-su") && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: ne,
						className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]",
						children: "💾 LƯU THAY ĐỔI"
					})
				]
			}),
			p && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => m(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: [
								"Xác nhận đã giao ",
								u.id,
								"?"
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14.5px] text-slate-600 mt-1.5",
							children: [
								"Khách ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: u.customer }),
								" đã ký nhận đủ ",
								/* @__PURE__ */ (0, F.jsxs)("b", { children: [u.cargo.packs, " kiện"] }),
								" tại ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: u.importInfo.deliveryAddr }),
								"? Sau xác nhận, lô chuyển sang “Đã giao” và mở được PXK."
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => m(!1),
								children: "Chưa, để sau"
							}), /* @__PURE__ */ (0, F.jsx)(xa, {
								onClick: ie,
								children: "✅ ĐÃ GIAO"
							})]
						})
					]
				})]
			}),
			d && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => f(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Ghi nhận thanh toán — ", u.id]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[13.5px] text-slate-500",
							children: ["Còn phải thu: ", /* @__PURE__ */ (0, F.jsx)("b", {
								className: "text-red-700",
								children: da(u.finance.outstanding, k)
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Loại khoản",
								children: /* @__PURE__ */ (0, F.jsxs)("select", {
									value: v,
									onChange: (e) => y(e.target.value),
									className: W(),
									children: [
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tiền khách" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tạm ứng" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu nốt công nợ" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Trả đối tác" })
									]
								})
							}), /* @__PURE__ */ (0, F.jsx)(U, {
								label: `Số tiền (${k})`,
								required: !0,
								error: h ? void 0 : "Nhập số tiền — VD: 150000000",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: h,
									onChange: (e) => g(e.target.value),
									inputMode: "numeric",
									placeholder: "VD: 150000000",
									className: W(h ? "ok" : "missing")
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: [
								"Ghi theo đồng tiền của lô (",
								k,
								") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai."
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => f(!1),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(xa, {
								onClick: M,
								children: "💾 LƯU KHOẢN THU"
							})]
						})
					]
				})]
			}),
			w > 0 && /* @__PURE__ */ (0, F.jsx)("span", { className: "hidden" })
		]
	});
}
//#endregion
//#region src/pages/CreateShipment.tsx
function Ia() {
	let { customers: e, quotes: t, contracts: n, dispatch: r, toast: i } = Xn(), a = xt(), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)(""), [u, d] = (0, _.useState)(""), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)("Truck"), [g, v] = (0, _.useState)("DAP"), [y, b] = (0, _.useState)(""), [x, S] = (0, _.useState)(""), [C, w] = (0, _.useState)(""), [T, E] = (0, _.useState)(""), [D, O] = (0, _.useState)(""), k = (0, _.useMemo)(() => t.filter((e) => (e.status || "").toLowerCase().includes("accept") || (e.status || "").toLowerCase().includes("chốt")), [t]), ee = t.find((e) => e.id === o) ?? null, te = (r) => {
		s(r);
		let a = t.find((e) => e.id === r);
		if (!a) return;
		let o = e.find((e) => e.name === a.customer);
		o && d(o.name);
		let c = n.find((e) => e.company === a.customer);
		c && p(c.id), i("Đã nạp báo giá " + r, "Giá trị và khách hàng đã được điền sẵn từ báo giá đã chốt.", "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1000px]",
		children: [/* @__PURE__ */ (0, F.jsxs)(P, {
			to: "/lo-hang",
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, F.jsx)(pr, { size: 17 }), " Về danh sách lô"]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
			children: [/* @__PURE__ */ (0, F.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }), /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "p-4 md:p-6",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						title: "Tạo Lô Hàng Mới",
						sub: "Bắt đầu từ báo giá đã chốt để tự điền, rồi chỉ bổ sung phần còn thiếu. Ghi bằng writer hiện có của Logistics."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-2xl bg-blue-50 border border-blue-200 p-4 mb-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-[15px] text-blue-900 flex items-center gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 17 }), " 1 · Chọn báo giá đã chốt (không bắt buộc)"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3",
								children: [k.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[14px] text-blue-800",
									children: "Chưa có báo giá đã chốt trong dữ liệu hiện tại — có thể nhập tay bên dưới."
								}), k.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => te(e.id),
									className: B("touch-target text-left rounded-xl border-2 bg-white p-3.5 lift", o === e.id ? "border-[#1e5aa8]" : "border-slate-200"),
									children: [
										/* @__PURE__ */ (0, F.jsxs)("p", {
											className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-1.5",
											children: [
												/* @__PURE__ */ (0, F.jsx)(Yr, {
													size: 16,
													className: "text-emerald-600"
												}),
												" ",
												e.id
											]
										}),
										/* @__PURE__ */ (0, F.jsxs)("p", {
											className: "text-[13.5px] text-slate-600 mt-0.5",
											children: [
												e.customer,
												" · ",
												V(e.status)
											]
										}),
										/* @__PURE__ */ (0, F.jsxs)("p", {
											className: "text-[13.5px] font-bold text-[#1e5aa8] mt-1",
											children: [
												la(e.total),
												" ",
												e.currency ?? "VND"
											]
										})
									]
								}, e.id))]
							}),
							ee && /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13.5px] text-blue-900 mt-3",
								children: [
									"Đã chọn ",
									/* @__PURE__ */ (0, F.jsx)("b", { children: ee.id }),
									" — Quote Estimate chỉ dùng để điền trước; Finance Actual sẽ nhập riêng ở tab Tài chính của lô."
								]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-2xl border-2 border-slate-200 p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)(Ci, { size: 17 }), " 2 · Thông tin lô"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Mã lô (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: c,
											onChange: (e) => l(e.target.value.toUpperCase()),
											placeholder: "LO-0470",
											className: W(c.trim() ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Khách hàng (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, F.jsxs)("select", {
											value: u,
											onChange: (e) => d(e.target.value),
											className: W(u ? "ok" : "missing"),
											children: [/* @__PURE__ */ (0, F.jsx)("option", {
												value: "",
												children: "-- Chọn khách hàng --"
											}), e.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
												value: e.name,
												children: [e.name, e.mst ? ` · MST ${e.mst}` : ""]
											}, e.name))]
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Hợp đồng liên kết",
										children: /* @__PURE__ */ (0, F.jsxs)("select", {
											value: f,
											onChange: (e) => p(e.target.value),
											className: W(),
											children: [/* @__PURE__ */ (0, F.jsx)("option", {
												value: "",
												children: "-- Chưa liên kết --"
											}), n.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
												value: e.id,
												children: [
													e.id,
													" · ",
													e.company
												]
											}, e.id))]
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Mode / Incoterm",
										children: /* @__PURE__ */ (0, F.jsxs)("div", {
											className: "flex gap-2",
											children: [/* @__PURE__ */ (0, F.jsx)("select", {
												value: m,
												onChange: (e) => h(e.target.value),
												className: W(),
												children: [
													"Truck",
													"Sea",
													"Air",
													"Rail"
												].map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
													value: e,
													children: e
												}, e))
											}), /* @__PURE__ */ (0, F.jsx)("select", {
												value: g,
												onChange: (e) => v(e.target.value),
												className: W(),
												children: [
													"EXW",
													"FCA",
													"FOB",
													"CIF",
													"DAP",
													"DDP"
												].map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
													value: e,
													children: e
												}, e))
											})]
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Nơi lấy hàng (POL)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: y,
											onChange: (e) => b(e.target.value),
											placeholder: "Bằng Tường (Quảng Tây)",
											className: W()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Điểm đến (POD)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: x,
											onChange: (e) => S(e.target.value),
											placeholder: "Hữu Nghị (Lạng Sơn)",
											className: W()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "Ngày khởi hành (ETD)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: C,
											onChange: (e) => w(e.target.value),
											placeholder: "DD/MM/YYYY",
											className: W()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(U, {
										label: "SĐT người nhận",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: D,
											onChange: (e) => O(e.target.value),
											placeholder: "0912…",
											className: W()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)("div", {
										className: "md:col-span-2",
										children: /* @__PURE__ */ (0, F.jsx)(U, {
											label: "Địa chỉ giao hàng",
											children: /* @__PURE__ */ (0, F.jsx)("input", {
												value: T,
												onChange: (e) => E(e.target.value),
												placeholder: "Kho khách — KCN…",
												className: W()
											})
										})
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-col sm:flex-row gap-2.5 mt-4",
								children: [/* @__PURE__ */ (0, F.jsxs)(ba, {
									onClick: () => {
										if (!c.trim()) {
											i("Thiếu mã lô", "Nhập mã lô (ví dụ LO-0470) rồi bấm Tạo lô hàng.", "red");
											return;
										}
										if (!u.trim()) {
											i("Thiếu khách hàng", "Chọn khách hàng — backend từ chối lô không có khách.", "red");
											return;
										}
										r("shipment_create", {
											shipmentId: c.trim().toUpperCase(),
											customerId: e.find((e) => e.name === u)?.name ?? "",
											customer: u,
											contractId: f.trim(),
											currency: "VND",
											transport: {
												mode: m,
												incoterm: g,
												pol: y.trim(),
												pod: x.trim(),
												etd: C.trim()
											},
											delivery: {
												addr: T.trim(),
												phone_receiver: D.trim()
											}
										}) ? (i("Đã gửi yêu cầu tạo " + c.trim().toUpperCase(), "Backend validate + ghi + audit. Mã trùng sẽ bị từ chối.", "green"), a("/lo-hang")) : i("Không gửi được", "Component chưa kết nối backend.", "red");
									},
									className: "flex-1",
									children: ["TẠO LÔ HÀNG ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
								}), /* @__PURE__ */ (0, F.jsx)(P, {
									to: "/lo-hang",
									className: "btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]",
									children: "Hủy"
								})]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] text-slate-500 mt-3",
								children: [
									"Lô được ghi qua writer hiện có của Logistics, có audit. Mã lô trùng sẽ bị từ chối. Các trường để trống được giữ là ",
									/* @__PURE__ */ (0, F.jsx)("b", { children: "không xác định" }),
									", không bị ép về 0."
								]
							})
						]
					})
				]
			})]
		})]
	});
}
//#endregion
//#region src/pages/Tracking.tsx
function La() {
	let { shipments: e } = Xn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(""), a = (0, _.useMemo)(() => e.filter((e) => !r || (e.id + e.customer + (e.transport?.containerNo ?? "")).toLowerCase().includes(r.toLowerCase())), [e, r]), o = e.find((e) => e.id === t) ?? a[0] ?? null, s = o?.tracking ?? null;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
			children: [/* @__PURE__ */ (0, F.jsx)(ya, {
				title: "Theo Dõi Vận Chuyển",
				sub: "Hiện trạng và mốc vận chuyển có thật từ dữ liệu lô hàng. Không mô phỏng vị trí GPS."
			}), /* @__PURE__ */ (0, F.jsx)("input", {
				value: r,
				onChange: (e) => i(e.target.value),
				placeholder: "Lọc theo mã lô, khách, biển số / container…",
				className: "w-full rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none"
			})]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4",
			children: [/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "p-3.5 border-b border-slate-200",
					children: /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "font-extrabold text-[15px] text-[#0f2a4a]",
						children: [
							"Lô hàng (",
							a.length,
							")"
						]
					})
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "divide-y divide-slate-100 max-h-[620px] overflow-y-auto",
					children: [a.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
						className: "p-6 text-center text-slate-500 text-[14px]",
						children: "Không có lô nào khớp."
					}), a.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: () => n(e.id),
						className: B("touch-target w-full text-left p-3.5 hover:bg-slate-50", o?.id === e.id ? "bg-blue-50" : ""),
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2",
								children: [
									/* @__PURE__ */ (0, F.jsx)(va, { tone: e.statusTone }),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[15px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: e.statusTone,
										size: "sm",
										children: e.status
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13.5px] text-slate-600 mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12.5px] text-slate-400 mt-0.5 truncate",
								children: V(e.route)
							})
						]
					}, e.id))]
				})]
			}), /* @__PURE__ */ (0, F.jsx)("div", {
				className: "space-y-4",
				children: !o || !s ? /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-10 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-extrabold text-[18px]",
						children: "Chọn một lô để xem hành trình"
					}), /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-slate-500 mt-1 text-[14.5px]",
						children: "Dữ liệu theo dõi lấy trực tiếp từ trạng thái vận chuyển của lô."
					})]
				}) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [
								/* @__PURE__ */ (0, F.jsx)(Gi, {
									size: 20,
									className: "text-[#1e5aa8]"
								}),
								/* @__PURE__ */ (0, F.jsxs)("h2", {
									className: "font-extrabold text-[19px] text-[#0f2a4a]",
									children: [
										o.id,
										" · ",
										o.customer
									]
								}),
								/* @__PURE__ */ (0, F.jsx)(H, {
									tone: s.statusTone,
									children: s.status
								}),
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: `/lo-hang/${o.id}`,
									className: "ml-auto btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px]",
									children: "Mở 360°"
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Hãng vận chuyển"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[15px] text-[#0f2a4a] mt-0.5",
										children: V(s.carrier)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Mã vận đơn / xe"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[15px] text-[#0f2a4a] mt-0.5",
										children: V(s.reference)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Tra cứu hãng"
									}), s.trackingUrl ? /* @__PURE__ */ (0, F.jsxs)("a", {
										href: s.trackingUrl,
										target: "_blank",
										rel: "noreferrer",
										className: "inline-flex items-center gap-1.5 font-extrabold text-[14.5px] text-[#1e5aa8] mt-0.5",
										children: ["Mở trang hãng ", /* @__PURE__ */ (0, F.jsx)(Gr, { size: 15 })]
									}) : /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[15px] text-slate-400 mt-0.5",
										children: "—"
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 flex items-start gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(hi, {
								size: 17,
								className: "text-amber-700 mt-0.5 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13.5px] text-amber-900",
								children: s.positionNote
							})]
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center gap-2 mb-3",
							children: [/* @__PURE__ */ (0, F.jsx)(xi, {
								size: 19,
								className: "text-[#0f2a4a]"
							}), /* @__PURE__ */ (0, F.jsx)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
								children: "Mốc vận chuyển"
							})]
						}),
						s.milestones.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500",
							children: "Chưa có mốc nào được ghi nhận cho lô này."
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "relative pl-6",
							children: [/* @__PURE__ */ (0, F.jsx)("span", { className: "absolute left-[9px] top-2 bottom-2 w-0.5 bg-slate-200" }), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "space-y-3",
								children: s.milestones.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "relative",
									children: [/* @__PURE__ */ (0, F.jsx)("span", { className: B("absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white", e.done ? e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500" : "bg-slate-300") }), /* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl border border-slate-200 p-3.5",
										children: [/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "flex flex-wrap items-center gap-2",
											children: [
												/* @__PURE__ */ (0, F.jsx)("p", {
													className: "font-extrabold text-[15px] text-[#0f2a4a]",
													children: e.title
												}),
												/* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-[13px] font-bold text-slate-500",
													children: V(e.time)
												}),
												/* @__PURE__ */ (0, F.jsx)(H, {
													tone: e.done ? e.tone : "gray",
													size: "sm",
													children: e.done ? "Đã diễn ra" : "Chưa"
												})
											]
										}), e.desc && /* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[13.5px] text-slate-600 mt-1",
											children: e.desc
										})]
									})]
								}, `${e.title}-${t}`))
							})]
						})
					]
				})] })
			})]
		})]
	});
}
//#endregion
//#region src/pages/Customers.tsx
var Ra = {
	id: "",
	name: "",
	phone: "",
	email: "",
	contactPerson: "",
	taxCode: "",
	address: "",
	note: ""
};
function za() {
	let { customers: e, dispatch: t, toast: n, role: r } = Xn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(null), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(!1), [m, h] = (0, _.useState)(Ra), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)(""), x = (0, _.useMemo)(() => e.filter((e) => !i || (e.id + e.name + e.short + e.mst + e.taxCode + e.phone + e.email).toLowerCase().includes(i.toLowerCase())), [e, i]), S = (e, t) => h((n) => ({
		...n,
		[e]: t
	})), C = () => {
		h(Ra), s(!0);
	}, w = (e) => {
		h({
			id: e.id,
			name: e.name,
			phone: e.phone,
			email: e.email,
			contactPerson: e.contactPerson,
			taxCode: e.taxCode,
			address: e.address,
			note: e.note
		}), l(e);
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						icon: /* @__PURE__ */ (0, F.jsx)(Yi, { size: 18 }),
						title: "Khách Hàng",
						sub: "Tìm theo mã · tên · MST · SĐT · email — tạo, sửa, lưu trữ và import qua backend Logistics thật",
						right: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex gap-2",
							children: [/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => p(!0),
								className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(qi, { size: 17 }), " Import"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: C,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 18 }), " Khách mới"]
							})]
						})
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [/* @__PURE__ */ (0, F.jsx)(Ni, {
							size: 19,
							className: "ml-3.5 text-slate-400 shrink-0"
						}), /* @__PURE__ */ (0, F.jsx)("input", {
							value: i,
							onChange: (e) => a(e.target.value),
							placeholder: "Nhập mã (CUST-ANPHAT), tên (An Phát), MST…",
							className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [x.length, " khách hàng"]
							}),
							i ? /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
								" cho “",
								i,
								"”"
							] }) : null,
							" · Mỗi khách hiển thị: mã · MST · liên hệ · địa chỉ."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[880px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Mã KH" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Tên khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "MST" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Liên hệ" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Địa chỉ" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: x.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[220px]",
									children: e.name
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: V(e.taxCode) }),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block",
										children: V(e.contactPerson)
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-slate-500",
										children: V(e.phone)
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "max-w-[240px] text-[13px] text-slate-600",
									children: V(e.address)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => w(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 15 }), " Sửa"]
									}), r === "ADMIN" && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => d(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-red-200 text-red-700 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(dr, { size: 15 }), " Lưu trữ"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), x.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy khách hàng nào"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo khách mới."
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: C,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Khách mới"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [x.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[17px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsxs)(H, {
									tone: "blue",
									size: "sm",
									children: ["MST ", V(e.taxCode)]
								})]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.name
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[13px] text-slate-500",
								children: V(e.address)
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-1",
								children: [
									V(e.contactPerson),
									" · ",
									V(e.phone)
								]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => w(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 17 }), " SỬA"]
						}), r === "ADMIN" ? /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => d(e),
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-red-700 min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(dr, { size: 17 }), " LƯU TRỮ"]
						}) : /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/kinh-doanh-bao-gia",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: ["BÁO GIÁ ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
						})]
					})]
				}, e.id)), x.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy khách hàng nào"
					}), /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: C,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Khách mới"]
					})]
				})]
			}),
			(o || c) && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => {
						s(!1), l(null);
					}
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: c ? "Sửa khách hàng " + c.id : "Tạo khách hàng mới"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Mọi thay đổi đi qua backend Logistics (RBAC + audit)."
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Mã khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.id,
										disabled: !!c,
										onChange: (e) => S("id", e.target.value),
										placeholder: "VD: CUST-ABC",
										className: W(m.id ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Tên khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.name,
										onChange: (e) => S("name", e.target.value),
										placeholder: "Công ty / cá nhân",
										className: W(m.name ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Mã số thuế",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.taxCode,
										onChange: (e) => S("taxCode", e.target.value),
										placeholder: "MST",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Người liên hệ",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.contactPerson,
										onChange: (e) => S("contactPerson", e.target.value),
										placeholder: "Tên người liên hệ",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Số điện thoại",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.phone,
										onChange: (e) => S("phone", e.target.value),
										placeholder: "SĐT",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Email",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.email,
										onChange: (e) => S("email", e.target.value),
										placeholder: "email",
										className: W()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Địa chỉ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: m.address,
									onChange: (e) => S("address", e.target.value),
									placeholder: "Địa chỉ kho / văn phòng",
									className: W()
								})
							}), /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Ghi chú",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: m.note,
									onChange: (e) => S("note", e.target.value),
									placeholder: "Ghi chú nội bộ",
									className: W()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => {
									s(!1), l(null);
								},
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsxs)(xa, {
								onClick: () => {
									let e = m.id.trim().toUpperCase();
									if (!e || !m.name.trim()) {
										n("Thiếu thông tin", "Mã và tên khách hàng là bắt buộc.", "red");
										return;
									}
									c ? (t("customer_edit", {
										id: e,
										name: m.name.trim(),
										phone: m.phone.trim(),
										email: m.email.trim(),
										contact_person: m.contactPerson.trim(),
										tax_code: m.taxCode.trim(),
										address: m.address.trim(),
										note: m.note.trim()
									}), n("Đã gửi cập nhật " + e, "Backend ghi + audit; danh sách tự làm mới từ Logistics.", "green")) : (t("customer_create", {
										id: e,
										name: m.name.trim(),
										phone: m.phone.trim(),
										email: m.email.trim(),
										contactPerson: m.contactPerson.trim(),
										taxCode: m.taxCode.trim(),
										address: m.address.trim(),
										note: m.note.trim()
									}), n("Đã gửi tạo khách hàng " + e, "Backend ghi + audit; danh sách tự làm mới từ Logistics.", "green")), s(!1), l(null), h(Ra);
								},
								children: ["💾 ", c ? "LƯU THAY ĐỔI" : "TẠO KHÁCH HÀNG"]
							})]
						})
					]
				})]
			}),
			u && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => d(null)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[460px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: [
								"Lưu trữ ",
								u.id,
								"?"
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14.5px] text-slate-600 mt-1.5",
							children: [
								"Khách ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: u.name }),
								" sẽ bị soft-delete (không xóa vật lý). Chỉ Admin có quyền."
							]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Lý do lưu trữ",
								required: !0,
								error: g ? void 0 : "Nhập lý do trước khi lưu trữ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: g,
									onChange: (e) => v(e.target.value),
									placeholder: "VD: ngừng hợp tác",
									className: W(g ? "ok" : "missing")
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => d(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => {
									if (u) {
										if (!g.trim()) {
											n("Cần lý do lưu trữ", "Nhập lý do trước khi lưu trữ khách hàng.", "red");
											return;
										}
										t("customer_archive", {
											id: u.id,
											reason: g.trim()
										}), n("Đã gửi lưu trữ " + u.id, "Chỉ Admin có quyền; backend kiểm tra RBAC.", "blue"), d(null), v("");
									}
								},
								className: "btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-[15.5px] px-5 min-h-[48px]",
								children: "LƯU TRỮ"
							})]
						})
					]
				})]
			}),
			f && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => p(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: "Import khách hàng"
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[13.5px] text-slate-500",
							children: ["Mỗi dòng một khách: ", /* @__PURE__ */ (0, F.jsx)("b", { children: "Mã;Tên;MST;SĐT;Email;Địa chỉ" })]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Dữ liệu (mỗi dòng 1 khách)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: y,
									onChange: (e) => b(e.target.value),
									rows: 6,
									placeholder: "CUST-XYZ;Khách XYZ;0109999000;0988111222;xyz@example.com;KCN Test",
									className: B(W(), "font-mono text-[13.5px]")
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => p(!1),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(ba, {
								onClick: () => {
									let e = y.split(/\r?\n/).map((e) => e.trim()).filter(Boolean).map((e) => {
										let [t, n, r, i, a, o] = e.split(/[;,|\t]/).map((e) => e.trim());
										return {
											id: t,
											name: n,
											taxCode: r,
											phone: i,
											email: a,
											address: o
										};
									}).filter((e) => e.id && e.name);
									if (e.length === 0) {
										n("Không có dòng để import", "Mỗi dòng: Mã;Tên;MST;SĐT;Email;Địa chỉ", "red");
										return;
									}
									t("customer_import", { rows: e }), n("Đã gửi import " + e.length + " khách hàng", "Backend bỏ qua mã đã tồn tại.", "blue"), p(!1), b("");
								},
								children: "IMPORT"
							})]
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/SalesQuotes.tsx
var Ba = {
	DRAFT: "Nháp",
	READY_FOR_REVIEW: "Chờ review",
	SENT: "Đã gửi khách",
	ACCEPTED: "Khách chốt",
	REJECTED: "Từ chối",
	EXPIRED: "Hết hạn",
	READY_TO_CREATE_SHIPMENT: "Sẵn sàng tạo lô"
}, Va = {
	DRAFT: "gray",
	READY_FOR_REVIEW: "blue",
	SENT: "amber",
	ACCEPTED: "green",
	REJECTED: "red",
	EXPIRED: "gray",
	READY_TO_CREATE_SHIPMENT: "green"
}, Ha = {
	code: "",
	serviceName: "",
	unit: "Lần",
	qty: "1",
	currency: "VND",
	costUnit: "",
	sellUnit: "",
	taxPct: "8"
}, Ua = {
	customerId: "",
	salesOwner: "",
	origin: "",
	destination: "",
	route: "",
	incoterm: "EXW",
	transportMode: "Road",
	goodsDescription: "",
	expectedDeliveryDate: "",
	lines: [{ ...Ha }]
};
function Wa(e) {
	return {
		code: e.code,
		serviceName: e.serviceName,
		unit: e.unit,
		qty: e.qty == null ? "" : String(e.qty),
		currency: e.currency,
		costUnit: e.costUnit == null ? "" : String(e.costUnit),
		sellUnit: e.sellUnit == null ? "" : String(e.sellUnit),
		taxPct: e.taxPct == null ? "" : String(e.taxPct)
	};
}
function Ga() {
	let { quotes: e, customers: t, dispatch: n, toast: r } = Xn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("ALL"), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(Ua), m = (0, _.useMemo)(() => e.filter((e) => (o === "ALL" || e.status === o) && (!i || (e.id + e.quoteNo + e.customer + e.salesOwner + e.origin + e.destination).toLowerCase().includes(i.toLowerCase()))), [
		e,
		i,
		o
	]), h = ["ALL", ...Array.from(new Set(e.map((e) => e.status)))], g = (e, t) => p((n) => ({
		...n,
		[e]: t
	})), v = (e, t, n) => p((r) => ({
		...r,
		lines: r.lines.map((r, i) => i === e ? {
			...r,
			[t]: n
		} : r)
	})), y = () => p((e) => ({
		...e,
		lines: [...e.lines, { ...Ha }]
	})), b = (e) => p((t) => ({
		...t,
		lines: t.lines.length > 1 ? t.lines.filter((t, n) => n !== e) : t.lines
	})), x = () => {
		p({
			...Ua,
			lines: [{ ...Ha }],
			salesOwner: "Minh Tú"
		}), l(!0);
	}, S = (e) => {
		p({
			customerId: e.customerId,
			salesOwner: e.salesOwner,
			origin: e.origin,
			destination: e.destination,
			route: e.route,
			incoterm: e.incoterm,
			transportMode: e.transportMode,
			goodsDescription: e.goodsDescription,
			expectedDeliveryDate: e.expectedDeliveryDate,
			lines: e.serviceLines.length ? e.serviceLines.map(Wa) : [{ ...Ha }]
		}), d(e);
	}, C = () => f.lines.filter((e) => e.code.trim() || e.serviceName.trim()).map((e) => ({
		code: e.code.trim(),
		serviceName: e.serviceName.trim(),
		unit: e.unit.trim() || "Lần",
		qty: e.qty.trim() === "" ? "" : Number(e.qty),
		currency: e.currency.trim() || "VND",
		costUnit: e.costUnit.trim() === "" ? "" : Number(e.costUnit),
		sellUnit: e.sellUnit.trim() === "" ? "" : Number(e.sellUnit),
		taxPct: e.taxPct.trim() === "" ? "" : Number(e.taxPct)
	})), w = () => {
		if (!f.customerId) {
			r("Chưa chọn khách hàng", "Chọn khách hàng trước khi tạo báo giá.", "red");
			return;
		}
		let e = C();
		if (e.length === 0) {
			r("Thiếu dòng dịch vụ", "Cần ít nhất một dòng dịch vụ báo giá.", "red");
			return;
		}
		u ? (n("quote_edit", {
			id: u.id,
			sales_owner: f.salesOwner.trim(),
			origin: f.origin.trim(),
			destination: f.destination.trim(),
			route: f.route.trim(),
			incoterm: f.incoterm.trim(),
			goods_description: f.goodsDescription.trim(),
			expected_delivery_date: f.expectedDeliveryDate.trim(),
			serviceLines: e
		}), r("Đã gửi cập nhật " + u.id, "Backend tính lại giá bán + audit.", "green")) : (n("quote_create", {
			customerId: f.customerId,
			salesOwner: f.salesOwner.trim(),
			origin: f.origin.trim(),
			destination: f.destination.trim(),
			route: f.route.trim(),
			incoterm: f.incoterm.trim(),
			transportMode: f.transportMode.trim(),
			goodsDescription: f.goodsDescription.trim(),
			expectedDeliveryDate: f.expectedDeliveryDate.trim(),
			serviceLines: e
		}), r("Đã gửi tạo báo giá", "Backend tạo mã Q-… tự động, tính dự toán và audit.", "green")), l(!1), d(null);
	}, T = (e, t) => {
		n("quote_transition", {
			id: e.id,
			nextStatus: t
		}), r("Đã gửi chuyển trạng thái " + e.id, `→ ${Ba[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						icon: /* @__PURE__ */ (0, F.jsx)(Dr, { size: 18 }),
						title: "Kinh doanh · Báo giá",
						sub: "Báo giá (estimate) là dự toán LOG-C12 — tách bạch với tài chính thực thu/chi. Tìm theo mã · khách · tuyến.",
						right: /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: x,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 18 }), " Tạo báo giá"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: i,
								onChange: (e) => a(e.target.value),
								placeholder: "Nhập mã (Q-…), khách (An Phát), tuyến…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: h.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => s(e),
							className: B("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", o === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : Ba[e] ?? e
						}, e))
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [m.length, " báo giá"]
							}),
							" · Trạng thái do backend quyết định theo luồng chốt khách."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[960px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Mã báo giá" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Tuyến" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Sale" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Tổng (VND)" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: m.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("td", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsx)("span", {
									className: "block text-[12px] text-slate-400",
									children: e.quoteNo
								})] }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "max-w-[220px] text-[13px] text-slate-600",
									children: [
										V(e.origin),
										" → ",
										V(e.destination)
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: V(e.salesOwner) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-bold",
									children: la(e.sellingPriceTotalVnd ?? e.total, "VND")
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: Va[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex flex-wrap gap-1.5",
									children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => T(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: Ba[t] ?? t
									}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => S(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 14 }), " Sửa"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), m.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy báo giá nào"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Tạo báo giá từ khách hàng đã có."
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: x,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo báo giá"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [m.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[16px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsx)(H, {
									tone: Va[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								})]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									V(e.origin),
									" → ",
									V(e.destination)
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-[16px] mt-1.5",
								children: [la(e.sellingPriceTotalVnd ?? e.total, "VND"), " ₫"]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "border-t p-3 flex flex-wrap gap-2",
						children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => T(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: Ba[t] ?? t
						}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => S(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 14 }), " Sửa"]
						})]
					})]
				}, e.id)), m.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy báo giá nào"
					}), /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: x,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo báo giá"]
					})]
				})]
			}),
			(c || u) && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => {
						l(!1), d(null);
					}
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[760px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[92vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: u ? "Sửa báo giá " + u.id : "Tạo báo giá mới"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Dự toán chi phí & giá bán — đi qua backend LOG-C12 (tính toán + audit), không ghi sổ tài chính."
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: f.customerId,
										disabled: !!u,
										onChange: (e) => g("customerId", e.target.value),
										className: W(f.customerId ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, F.jsx)("option", {
											value: "",
											children: "-- Chọn khách --"
										}), t.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
											value: e.id,
											children: [
												e.name,
												" (",
												e.id,
												")"
											]
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Sale phụ trách",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.salesOwner,
										onChange: (e) => g("salesOwner", e.target.value),
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Nơi lấy (origin)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.origin,
										onChange: (e) => g("origin", e.target.value),
										placeholder: "VD: Bằng Tường (Quảng Tây)",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Nơi giao (destination)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.destination,
										onChange: (e) => g("destination", e.target.value),
										placeholder: "VD: KCN Quế Võ, Bắc Ninh",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Tuyến / cửa khẩu",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.route,
										onChange: (e) => g("route", e.target.value),
										placeholder: "VD: Hữu Nghị (Lạng Sơn)",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Incoterm",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.incoterm,
										onChange: (e) => g("incoterm", e.target.value),
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Phương thức",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.transportMode,
										onChange: (e) => g("transportMode", e.target.value),
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Ngày giao dự kiến",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.expectedDeliveryDate,
										onChange: (e) => g("expectedDeliveryDate", e.target.value),
										placeholder: "VD: 2026-09-20",
										className: W()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(U, {
							label: "Mô tả hàng hóa",
							children: /* @__PURE__ */ (0, F.jsx)("input", {
								value: f.goodsDescription,
								onChange: (e) => g("goodsDescription", e.target.value),
								placeholder: "VD: Linh kiện điện tử",
								className: B(W(), "mt-3")
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center justify-between mb-2",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-extrabold text-[15px] text-[#0f2a4a]",
									children: "Dòng dịch vụ"
								}), /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: y,
									className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
									children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 15 }), " Thêm dòng"]
								})]
							}), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "space-y-2",
								children: f.lines.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl border border-slate-200 p-3 bg-slate-50/60",
									children: [/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "grid grid-cols-2 md:grid-cols-4 gap-2",
										children: [
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Mã dịch vụ",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.code,
													onChange: (e) => v(t, "code", e.target.value),
													placeholder: "DV-VC-TQ",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Tên dịch vụ",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.serviceName,
													onChange: (e) => v(t, "serviceName", e.target.value),
													placeholder: "Cước xe TQ",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "ĐVT",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.unit,
													onChange: (e) => v(t, "unit", e.target.value),
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Số lượng",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.qty,
													onChange: (e) => v(t, "qty", e.target.value),
													inputMode: "numeric",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Giá vốn (unit)",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.costUnit,
													onChange: (e) => v(t, "costUnit", e.target.value),
													inputMode: "numeric",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Giá bán (unit)",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.sellUnit,
													onChange: (e) => v(t, "sellUnit", e.target.value),
													inputMode: "numeric",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Thuế %",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.taxPct,
													onChange: (e) => v(t, "taxPct", e.target.value),
													inputMode: "numeric",
													className: W()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(U, {
												label: "Tiền tệ",
												children: /* @__PURE__ */ (0, F.jsxs)("select", {
													value: e.currency,
													onChange: (e) => v(t, "currency", e.target.value),
													className: W(),
													children: [
														/* @__PURE__ */ (0, F.jsx)("option", { children: "VND" }),
														/* @__PURE__ */ (0, F.jsx)("option", { children: "USD" }),
														/* @__PURE__ */ (0, F.jsx)("option", { children: "CNY" })
													]
												})
											})
										]
									}), f.lines.length > 1 && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => b(t),
										className: "mt-2 inline-flex items-center gap-1 text-[13px] font-bold text-red-600",
										children: [/* @__PURE__ */ (0, F.jsx)(Vi, { size: 14 }), " Xóa dòng"]
									})]
								}, t))
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => {
									l(!1), d(null);
								},
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsxs)(xa, {
								onClick: w,
								children: ["💾 ", u ? "LƯU BÁO GIÁ" : "TẠO BÁO GIÁ"]
							})]
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/Agreements.tsx
var Ka = {
	DRAFT: "Nháp",
	REVIEWING: "Đang review",
	AGREED: "Đã đồng ý",
	REVISED: "Đã sửa đổi",
	VOID: "Vô hiệu"
}, qa = {
	DRAFT: "gray",
	REVIEWING: "blue",
	AGREED: "green",
	REVISED: "amber",
	VOID: "red"
}, Ja = [
	"accepted_quotation",
	"signed_contract",
	"customer_confirmation",
	"entrusted_documentation"
], Ya = {
	accepted_quotation: "Báo giá được khách chốt",
	signed_contract: "Hợp đồng đã ký",
	customer_confirmation: "Khách xác nhận (email/tin nhắn)",
	entrusted_documentation: "Chứng từ ủy thác nhập khẩu"
};
function Xa() {
	let { agreements: e, quotes: t, dispatch: n, toast: r } = Xn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("ALL"), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)({}), x = (0, _.useMemo)(() => e.filter((e) => (o === "ALL" || e.status === o) && (!i || (e.id + e.agreementNo + e.customer + e.quoteReference).toLowerCase().includes(i.toLowerCase()))), [
		e,
		i,
		o
	]), S = ["ALL", ...Array.from(new Set(e.map((e) => e.status)))], C = (0, _.useMemo)(() => {
		let n = new Set(e.map((e) => e.quoteId).filter(Boolean));
		return t.filter((e) => ["ACCEPTED", "READY_TO_CREATE_SHIPMENT"].includes(e.status) && !n.has(e.id));
	}, [t, e]), w = () => {
		p(""), l(!0);
	}, T = (e) => {
		h((e.assumptions || []).join("\n")), v((e.unresolvedIssues || []).join("\n"));
		let t = {};
		for (let n of Ja) t[n] = !!e.evidence?.[n];
		b(t), d(e);
	}, E = () => {
		if (!f) {
			r("Chưa chọn báo giá", "Thỏa thuận chỉ được tạo từ báo giá đã khách chốt (ACCEPTED).", "red");
			return;
		}
		n("agreement_create", { quoteId: f }), r("Đã gửi tạo thỏa thuận", "Backend đóng băng điều khoản thương mại từ báo giá chốt.", "green"), l(!1);
	}, D = () => {
		u && (n("agreement_edit", {
			id: u.id,
			assumptions: m.split("\n").map((e) => e.trim()).filter(Boolean),
			unresolved_issues: g.split("\n").map((e) => e.trim()).filter(Boolean),
			evidence: {
				...Ja.reduce((e, t) => ({
					...e,
					[t]: !!y[t]
				}), {}),
				notes: "",
				source: "Bằng chứng đánh dấu thủ công qua work desk; không suy diễn 'đã ký' từ tên file."
			}
		}), r("Đã gửi cập nhật " + u.id, "Backend ghi + audit; bàn giao được tính lại.", "green"), d(null));
	}, O = (e, t) => {
		n("agreement_transition", {
			id: e.id,
			nextStatus: t
		}), r("Đã gửi chuyển trạng thái " + e.id, `→ ${Ka[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						icon: /* @__PURE__ */ (0, F.jsx)(Yr, { size: 18 }),
						title: "Thỏa thuận mua bán · Bàn giao",
						sub: "Đóng băng điều khoản thương mại từ báo giá đã chốt — KHÔNG phải tài chính thực thu/chi",
						right: /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: w,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 18 }), " Tạo thỏa thuận"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: i,
								onChange: (e) => a(e.target.value),
								placeholder: "Nhập mã thỏa thuận, khách, báo giá nguồn…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: S.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => s(e),
							className: B("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", o === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : Ka[e] ?? e
						}, e))
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [x.length, " thỏa thuận"]
							}),
							" · Trạng thái & bàn giao do backend quyết định."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[960px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Mã thỏa thuận" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Báo giá nguồn" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Bàn giao" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: x.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("td", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsx)("span", {
									className: "block text-[12px] text-slate-400",
									children: e.agreementNo
								})] }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "text-[13px] text-slate-600",
									children: V(e.quoteReference)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: qa[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "max-w-[220px]",
									children: /* @__PURE__ */ (0, F.jsx)(H, {
										tone: e.handoff.state === "READY_FOR_OPERATIONS" ? "green" : e.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber",
										size: "sm",
										children: e.handoff.label
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex flex-wrap gap-1.5",
									children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => O(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: Ka[t] ?? t
									}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => T(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 14 }), " Sửa"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), x.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Chưa có thỏa thuận nào"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Tạo từ báo giá đã được khách chốt (ACCEPTED)."
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: w,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo thỏa thuận"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [x.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[16px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsx)(H, {
									tone: qa[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								})]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: ["Nguồn: ", V(e.quoteReference)]
							}),
							/* @__PURE__ */ (0, F.jsx)("div", {
								className: "mt-2",
								children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: e.handoff.state === "READY_FOR_OPERATIONS" ? "green" : e.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber",
									size: "sm",
									children: e.handoff.label
								})
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "border-t p-3 flex flex-wrap gap-2",
						children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => O(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: Ka[t] ?? t
						}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => T(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Ti, { size: 14 }), " Sửa"]
						})]
					})]
				}, e.id)), x.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Chưa có thỏa thuận nào"
					}), /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: w,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo thỏa thuận"]
					})]
				})]
			}),
			c && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => l(!1)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[520px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: "Tạo thỏa thuận từ báo giá chốt"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Chỉ báo giá ACCEPTED / sẵn sàng tạo lô mới dùng được."
						}),
						C.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4 text-[14px] text-amber-900",
							children: [
								"Chưa có báo giá ACCEPTED. Vào ",
								/* @__PURE__ */ (0, F.jsx)(P, {
									to: "/kinh-doanh-bao-gia",
									className: "font-bold underline",
									children: "Kinh doanh · Báo giá"
								}),
								" để chốt khách trước."
							]
						}) : /* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Báo giá nguồn",
								required: !0,
								children: /* @__PURE__ */ (0, F.jsxs)("select", {
									value: f,
									onChange: (e) => p(e.target.value),
									className: W(f ? "ok" : "missing"),
									children: [/* @__PURE__ */ (0, F.jsx)("option", {
										value: "",
										children: "-- Chọn báo giá đã chốt --"
									}), C.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
										value: e.id,
										children: [
											e.id,
											" · ",
											e.customer,
											" · ",
											la(e.sellingPriceTotalVnd ?? e.total),
											" ₫"
										]
									}, e.id))]
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => l(!1),
								children: "Hủy"
							}), C.length > 0 ? /* @__PURE__ */ (0, F.jsx)(xa, {
								onClick: E,
								children: "TẠO"
							}) : /* @__PURE__ */ (0, F.jsx)(ba, {
								onClick: () => {
									l(!1);
								},
								children: "ĐÓNG"
							})]
						})
					]
				})]
			}),
			u && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => d(null)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Sửa thỏa thuận ", u.id]
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Điều khoản thương mại & bằng chứng bàn giao — ghi qua backend, không phải tài chính."
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-extrabold text-[14.5px] text-[#0f2a4a] mb-2",
								children: "Bằng chứng chấp nhận"
							}), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "grid sm:grid-cols-2 gap-2",
								children: Ja.map((e) => /* @__PURE__ */ (0, F.jsxs)("label", {
									className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-3 cursor-pointer",
									children: [/* @__PURE__ */ (0, F.jsx)("input", {
										type: "checkbox",
										checked: !!y[e],
										onChange: (t) => b((n) => ({
											...n,
											[e]: t.target.checked
										})),
										className: "w-5 h-5 accent-[#0f2a4a]"
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "text-[14px] font-semibold text-slate-700",
										children: Ya[e]
									})]
								}, e))
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Giả định thương mại (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: m,
									onChange: (e) => h(e.target.value),
									rows: 4,
									className: W()
								})
							}), /* @__PURE__ */ (0, F.jsx)(U, {
								label: "Vấn đề chưa giải quyết (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: g,
									onChange: (e) => v(e.target.value),
									rows: 3,
									placeholder: "Các vấn đề chặn bàn giao vận hành",
									className: W()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
								onClick: () => d(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(ba, {
								onClick: D,
								children: "💾 LƯU THỎA THUẬN"
							})]
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/Contracts.tsx
function Za() {
	let { contracts: e } = Xn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)("ALL"), a = (0, _.useMemo)(() => e.filter((e) => (r === "ALL" || e.kind === r) && (!t || (e.id + e.contractNo + e.client + e.company + e.agent).toLowerCase().includes(t.toLowerCase()))), [
		e,
		t,
		r
	]), o = ["ALL", ...Array.from(new Set(e.map((e) => e.kind).filter(Boolean)))];
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(ya, {
						icon: /* @__PURE__ */ (0, F.jsx)(ti, { size: 18 }),
						title: "Hợp đồng",
						sub: "HDMB · HDNT · PL — tìm theo số hợp đồng, khách, công ty, đại lý",
						right: /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/hop-dong/moi",
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 18 }), " Tạo hợp đồng"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(Ni, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								placeholder: "Nhập số hợp đồng (HDMB-0306), khách (An Phát)…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: o.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => i(e),
							className: B("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", r === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : e
						}, e))
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [a.length, " hợp đồng"]
							}),
							" · Mở để xem hàng hóa, sinh chứng từ và liên kết lô."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[880px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Số hợp đồng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Loại" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Công ty · Đại lý" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Giá trị" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: a.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(P, {
									to: "/hop-dong/" + e.id,
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: "blue",
									size: "sm",
									children: e.kind || "—"
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.client || "—"
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "text-[13px] text-slate-600",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block",
										children: e.company || "—"
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-slate-400",
										children: e.agent || "—"
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-bold",
									children: la(e.value, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("div", {
									className: "flex gap-1.5",
									children: /* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/hop-dong/" + e.id,
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(qr, { size: 15 }), " MỞ"]
									})
								}) })
							]
						}, e.id)) })]
					})
				}), a.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy hợp đồng nào"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo hợp đồng mới."
						}),
						/* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/hop-dong/moi",
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo hợp đồng"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [a.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-extrabold text-[17px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, F.jsx)(H, {
									tone: "blue",
									size: "sm",
									children: e.kind || "—"
								})]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.client || "—"
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									e.company || "—",
									" · ",
									e.agent || "—"
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-extrabold text-[16px] mt-1.5",
								children: la(e.value, e.currency)
							})
						]
					}), /* @__PURE__ */ (0, F.jsx)("div", {
						className: "border-t",
						children: /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/hop-dong/" + e.id,
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: ["MỞ HỢP ĐỒNG ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
						})
					})]
				}, e.id)), a.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy hợp đồng nào"
					}), /* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/hop-dong/moi",
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 17 }), " Tạo hợp đồng"]
					})]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/ContractDetail.tsx
var Qa = [
	{
		id: "tong-quan",
		label: "Tổng quan",
		short: "Tổng quan"
	},
	{
		id: "hang-hoa",
		label: "Hàng hóa hợp đồng",
		short: "Hàng hóa"
	},
	{
		id: "chung-tu",
		label: "Chứng từ HDNT/PL/HDMB",
		short: "Chứng từ"
	},
	{
		id: "lo-lien-ket",
		label: "Lô liên kết",
		short: "Lô liên kết"
	}
], $a = {
	READY: "green",
	GENERATED: "blue",
	MISSING_INFO: "amber",
	NOT_APPLICABLE: "gray",
	OWNER_RULE_REQUIRED: "amber",
	BLOCKED: "red",
	DEFERRED: "gray",
	ISSUED: "green"
}, eo = {
	READY: "Sẵn sàng",
	GENERATED: "Đã sinh",
	MISSING_INFO: "Thiếu thông tin",
	NOT_APPLICABLE: "Không áp dụng",
	OWNER_RULE_REQUIRED: "Cần quy tắc chủ",
	BLOCKED: "Bị chặn",
	DEFERRED: "Hoãn lại",
	ISSUED: "Đã phát hành"
};
function to(e) {
	return {
		description: e.description,
		unit: e.unit,
		quantity: e.quantity == null ? "" : String(e.quantity),
		unitPrice: e.unitPrice == null ? "" : String(e.unitPrice)
	};
}
function no() {
	let { id: e } = Ct(), [t, n] = Bn(), r = t.get("tab") || "tong-quan", { contracts: i, authority: a, shipments: o, dispatch: s, toast: c } = Xn(), l = xt(), u = i.find((t) => t.id === e), [d, f] = (0, _.useState)({}), [p, m] = (0, _.useState)([]), [h, g] = (0, _.useState)(""), v = (e) => {
		f({
			company_id: e.companyId ?? "",
			agent_id: e.agentId ?? "",
			kind: e.kind ?? "",
			value: e.value == null ? "" : String(e.value),
			currency: e.currency || "VND",
			note: e.note ?? "",
			hdnt_no: e.identity?.hdntNo ?? "",
			hdnt_date: e.identity?.hdntDate ?? "",
			valid_from: e.identity?.validFrom ?? "",
			valid_to: e.identity?.validTo ?? "",
			pl_no: e.identity?.plNo ?? "",
			pl_date: e.identity?.plDate ?? "",
			hdmb_no: e.identity?.hdmbNo ?? "",
			hdmb_date: e.identity?.hdmbDate ?? ""
		}), m(e.goodsLines.length ? e.goodsLines.map(to) : [{
			description: "",
			unit: "",
			quantity: "",
			unitPrice: ""
		}]);
	};
	if ((0, _.useEffect)(() => {
		u && v(u);
	}, [u?.id]), !u) return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "font-extrabold text-[19px]",
				children: ["Không tìm thấy hợp đồng ", e]
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "text-slate-500 mt-1 text-[15px]",
				children: "Số hợp đồng có thể sai. Về danh sách để tìm lại."
			}),
			/* @__PURE__ */ (0, F.jsx)(P, {
				to: "/hop-dong",
				className: "btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center",
				children: "Về danh sách hợp đồng"
			})
		]
	});
	let y = (e, t) => f((n) => ({
		...n,
		[e]: t
	})), b = (e, t, n) => m((r) => r.map((r, i) => i === e ? {
		...r,
		[t]: n
	} : r)), x = () => m((e) => [...e, {
		description: "",
		unit: "",
		quantity: "",
		unitPrice: ""
	}]), S = (e) => m((t) => t.length > 1 ? t.filter((t, n) => n !== e) : t), C = () => {
		s("contract_save", {
			id: u.id,
			company_id: d.company_id.trim(),
			agent_id: d.agent_id.trim(),
			kind: d.kind.trim(),
			currency: d.currency.trim(),
			note: d.note.trim(),
			value: d.value.trim(),
			hdnt_no: d.hdnt_no.trim(),
			hdnt_date: d.hdnt_date.trim(),
			valid_from: d.valid_from.trim(),
			valid_to: d.valid_to.trim(),
			pl_no: d.pl_no.trim(),
			pl_date: d.pl_date.trim(),
			hdmb_no: d.hdmb_no.trim(),
			hdmb_date: d.hdmb_date.trim()
		}), c("Đã gửi lưu " + u.id, "Backend ghi danh tính pháp lý + audit; đọc lại từ Logistics.", "green");
	}, w = () => {
		let e = p.map((e) => ({
			description: e.description.trim(),
			unit: e.unit.trim(),
			quantity: e.quantity.trim(),
			unitPrice: e.unitPrice.trim()
		}));
		s("contract_goods_save", {
			id: u.id,
			goodsLines: e
		}), c("Đã gửi lưu hàng hóa " + u.id, "Blank số lượng/đơn giá = UNKNOWN (không bao giờ thành 0).", "green");
	}, T = () => {
		s("contract_docgen_generate", { id: u.id }), c("Đã gửi sinh chứng từ " + u.id, "core.docgen kiểm tra threshold 50 triệu & danh tính pháp lý rồi sinh Office thật.", "blue");
	}, E = (e, t) => {
		s("contract_docgen_issue", {
			documentId: e,
			revision: t
		}), c("Đã gửi phát hành " + e, "Chứng từ ISSUED sẽ bất biến (không sửa/xóa).", "blue");
	}, D = () => {
		let e = h.trim().toUpperCase();
		if (!e) {
			c("Thiếu mã lô", "Nhập mã lô để liên kết (VD: LO-0306).", "red");
			return;
		}
		s("contract_shipment_link", {
			id: u.id,
			shipmentId: e
		}), c("Đã gửi liên kết " + e, "Liên kết N:M hợp đồng ↔ lô qua backend.", "green"), g("");
	};
	u.goodsTotals?.total_after_vat;
	let O = u.thresholdVnd ?? 5e7, k = u.goodsTotals != null && u.goodsTotals.total_after_vat < O, ee = o.filter((e) => !u.linkedShipments.some((t) => t.id === e.id));
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("button", {
				onClick: () => l(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, F.jsx)(pr, { size: 17 }), " Quay lại"]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [
					/* @__PURE__ */ (0, F.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4 md:p-6",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap items-center gap-2",
								children: [
									/* @__PURE__ */ (0, F.jsx)("h1", {
										className: "text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]",
										children: u.id
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: "blue",
										size: "sm",
										children: u.kind || "—"
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: u.statusTone,
										size: "sm",
										children: u.status
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[15.5px] mt-1",
								children: u.client || "—"
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-2 md:grid-cols-4 gap-x-6 mt-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Công ty (mua)",
										value: V(u.company)
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Đại lý (bán)",
										value: V(u.agent)
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Giá trị",
										value: ua(u.value)
									}),
									/* @__PURE__ */ (0, F.jsx)(Ta, {
										label: "Số lô liên kết",
										value: String(u.linkedShipments.length)
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						id: "contract-tabs",
						className: "px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3",
						children: Qa.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => n({ tab: e.id }),
							className: B("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", r === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: "hidden md:inline",
								children: e.label
							}), /* @__PURE__ */ (0, F.jsx)("span", {
								className: "md:hidden",
								children: e.short
							})]
						}, e.id))
					})
				]
			}),
			r === "tong-quan" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3",
					children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
						children: [/* @__PURE__ */ (0, F.jsx)(ti, {
							size: 19,
							className: "text-[#1e5aa8]"
						}), " Danh tính pháp lý"]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid sm:grid-cols-2 gap-3",
						children: [
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Số HDNT",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdnt_no,
									onChange: (e) => y("hdnt_no", e.target.value),
									placeholder: "HDNT-…/2026",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Ngày HDNT",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdnt_date,
									onChange: (e) => y("hdnt_date", e.target.value),
									placeholder: "2026-09-01",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Hiệu lực từ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.valid_from,
									onChange: (e) => y("valid_from", e.target.value),
									placeholder: "2026-09-01",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Hiệu lực đến",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.valid_to,
									onChange: (e) => y("valid_to", e.target.value),
									placeholder: "2027-08-31",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Số PL",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.pl_no,
									onChange: (e) => y("pl_no", e.target.value),
									placeholder: "PL-…/2026",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Ngày PL",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.pl_date,
									onChange: (e) => y("pl_date", e.target.value),
									placeholder: "2026-09-02",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Số HDMB",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdmb_no,
									onChange: (e) => y("hdmb_no", e.target.value),
									placeholder: "HDMB-…/2026",
									className: W()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(U, {
								label: "Ngày HDMB",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdmb_date,
									onChange: (e) => y("hdmb_date", e.target.value),
									placeholder: "2026-09-03",
									className: W()
								})
							})
						]
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(_r, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Đối tác & thông tin chung"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Công ty (bên mua)",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.company_id,
										onChange: (e) => y("company_id", e.target.value),
										className: W(d.company_id ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, F.jsx)("option", {
											value: "",
											children: "-- Chọn công ty --"
										}), a.companies.map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
											value: e.id,
											children: e.legalName
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Đại lý (bên bán)",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.agent_id,
										onChange: (e) => y("agent_id", e.target.value),
										className: W(d.agent_id ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, F.jsx)("option", {
											value: "",
											children: "-- Chọn đại lý --"
										}), a.agents.map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
											value: e.id,
											children: e.legalName
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Loại",
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.kind,
										onChange: (e) => y("kind", e.target.value),
										className: W(),
										children: [
											/* @__PURE__ */ (0, F.jsx)("option", {
												value: "HDMB",
												children: "HDMB"
											}),
											/* @__PURE__ */ (0, F.jsx)("option", {
												value: "HDNT",
												children: "HDNT"
											}),
											/* @__PURE__ */ (0, F.jsx)("option", {
												value: "PL",
												children: "PL"
											})
										]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Giá trị (VND)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.value,
										onChange: (e) => y("value", e.target.value),
										inputMode: "numeric",
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Tiền tệ",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.currency,
										onChange: (e) => y("currency", e.target.value),
										className: W()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(U, {
									label: "Ghi chú",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.note,
										onChange: (e) => y("note", e.target.value),
										className: W()
									})
								})
							]
						}),
						u.parties && (u.parties.company || u.parties.agent) && /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 pt-1",
							children: [u.parties.company && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "rounded-xl bg-slate-50 border p-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase text-slate-400",
										children: "Công ty — hồ sơ pháp lý"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-bold text-[14px] mt-1",
										children: u.parties.company.legalName
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											u.parties.company.legalCode,
											" · ",
											u.parties.company.legalAddress
										]
									})
								]
							}), u.parties.agent && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "rounded-xl bg-slate-50 border p-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase text-slate-400",
										children: "Đại lý — hồ sơ pháp lý"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-bold text-[14px] mt-1",
										children: u.parties.agent.legalName
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											u.parties.agent.legalCode,
											" · ",
											u.parties.agent.legalAddress
										]
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)(ba, {
							onClick: C,
							className: "w-full",
							children: "💾 LƯU TỔNG QUAN"
						})
					]
				})]
			}),
			r === "hang-hoa" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center justify-between mb-3",
							children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)(Ci, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Hàng hóa hợp đồng"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: x,
								className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
								children: [/* @__PURE__ */ (0, F.jsx)(ki, { size: 15 }), " Thêm dòng"]
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "overflow-x-auto -mx-1",
							children: /* @__PURE__ */ (0, F.jsxs)("table", {
								className: "tbl w-full text-[14px] min-w-[720px]",
								children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, F.jsx)("th", {
										className: "w-10",
										children: "STT"
									}),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Mô tả hàng hóa" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Đơn vị" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Số lượng" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Đơn giá (VND)" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "VAT" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Thành tiền" }),
									/* @__PURE__ */ (0, F.jsx)("th", {})
								] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: p.map((e, t) => {
									let n = e.quantity.trim() === "" ? null : Number(e.quantity), r = e.unitPrice.trim() === "" ? null : Number(e.unitPrice), i = n != null && r != null ? n * r : null;
									return /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-bold text-slate-400",
											children: t + 1
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.description,
											onChange: (e) => b(t, "description", e.target.value),
											placeholder: "Mô tả hàng hóa",
											className: W()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.unit,
											onChange: (e) => b(t, "unit", e.target.value),
											placeholder: "Bộ / chiếc",
											className: W()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.quantity,
											onChange: (e) => b(t, "quantity", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: W()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.unitPrice,
											onChange: (e) => b(t, "unitPrice", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: W()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "text-slate-600",
											children: "8%"
										}),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-bold whitespace-nowrap",
											children: ca(i) ? "—" : la(i)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("button", {
											onClick: () => S(t),
											className: "touch-target inline-flex items-center justify-center w-9 h-9 rounded-lg text-red-600 hover:bg-red-50",
											"aria-label": "Xóa dòng",
											children: /* @__PURE__ */ (0, F.jsx)(Vi, { size: 16 })
										}) })
									] }, t);
								}) })]
							})
						}),
						/* @__PURE__ */ (0, F.jsx)(ba, {
							onClick: w,
							className: "w-full mt-3",
							children: "💾 LƯU HÀNG HÓA"
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-2",
							children: "Số lượng / đơn giá để trống = UNKNOWN (“—”), không bao giờ tự thành 0. Dòng trống hoàn toàn sẽ bị bỏ qua."
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
							children: "Tổng & quyết định chứng từ (backend)"
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 md:grid-cols-4 gap-3 text-center",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-slate-500 font-semibold",
										children: "Tổng trước thuế"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px]",
										children: la(u.goodsTotals?.subtotal)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-slate-500 font-semibold",
										children: "VAT 8%"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px]",
										children: la(u.goodsTotals?.vat_amount)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-blue-700 font-semibold",
										children: "Sau thuế"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px] text-blue-700",
										children: la(u.goodsTotals?.total_after_vat)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-violet-50 border border-violet-200 p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-violet-700 font-semibold",
										children: "Ngưỡng"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px] text-violet-700",
										children: la(O)
									})]
								})
							]
						}),
						u.goodsTotals == null ? /* @__PURE__ */ (0, F.jsx)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13.5px] text-amber-900",
							children: "Chưa có tổng đáng tin cậy (có dòng UNKNOWN) — không thể thay bằng 0, chứng từ bị chặn cho tới khi đủ dữ liệu."
						}) : /* @__PURE__ */ (0, F.jsxs)("div", {
							className: B("mt-3 rounded-xl border-2 p-3.5", k ? "border-emerald-300 bg-emerald-50" : "border-blue-300 bg-blue-50"),
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-extrabold text-[15px]",
								children: k ? "Sau thuế < 50.000.000 ₫ → HDNT + PL" : "Sau thuế ≥ 50.000.000 ₫ → HDMB"
							}), /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13.5px] mt-0.5",
								children: ["Áp dụng: ", /* @__PURE__ */ (0, F.jsx)("b", { children: u.applicableDocuments.length ? u.applicableDocuments.join(" + ") : "—" })]
							})]
						})
					]
				})]
			}),
			r === "chung-tu" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center justify-between mb-3",
							children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)(Yr, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Chứng từ HDNT · PL · HDMB"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: T,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(zi, { size: 17 }), " SINH CHỨNG TỪ"]
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13.5px] text-slate-500 mb-3",
							children: "Quy tắc backend: VAT 8% · VND · làm tròn nửa lên từng đồng · sau thuế < 50M → HDNT + PL, ≥ 50M → HDMB. Chỉ sinh khi READY."
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid sm:grid-cols-2 gap-2.5",
							children: u.docCards.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "rounded-xl border-2 p-3.5",
								style: { borderColor: "var(--slate-200)" },
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "flex items-center justify-between gap-2",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "font-extrabold text-[14.5px] text-[#0f2a4a]",
											children: e.document_type
										}), /* @__PURE__ */ (0, F.jsx)(H, {
											tone: $a[e.state] ?? "gray",
											size: "sm",
											children: eo[e.state] ?? e.state
										})]
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[13px] text-slate-600 mt-1",
										children: e.reason
									}),
									e.missing.length > 0 && /* @__PURE__ */ (0, F.jsx)("ul", {
										className: "mt-1.5 text-[12.5px] text-amber-800 list-disc pl-4 space-y-0.5",
										children: e.missing.map((e) => /* @__PURE__ */ (0, F.jsx)("li", { children: e }, e))
									})
								]
							}, e.document_type))
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
						children: "Chứng từ đã sinh — tải về / phát hành / lịch sử"
					}), u.documents.length === 0 ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Chưa có chứng từ nào. Nhập hàng hóa rồi bấm “SINH CHỨNG TỪ”."
					}) : /* @__PURE__ */ (0, F.jsx)("div", {
						className: "space-y-2",
						children: u.documents.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2.5 rounded-xl border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: B("w-9 h-9 rounded-lg grid place-items-center shrink-0", e.status === "ISSUED" ? "bg-emerald-600 text-white" : "bg-blue-100 text-blue-700"),
									children: e.status === "ISSUED" ? /* @__PURE__ */ (0, F.jsx)(Fr, { size: 18 }) : /* @__PURE__ */ (0, F.jsx)(ti, { size: 18 })
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex-1 min-w-[180px]",
									children: [/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "font-bold text-[14.5px] text-[#0f2a4a]",
										children: [
											e.documentTypeLabel,
											" · R",
											e.revision
										]
									}), /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											e.fileName,
											" · ",
											e.status,
											" · ",
											e.generatedBy ? "bởi " + e.generatedBy : ""
										]
									})]
								}),
								e.downloadAvailable && e.downloadBase64 && /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => ga(e.fileName, e.downloadBase64, e.mime),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, F.jsx)(Ur, { size: 16 }), " Tải"]
								}),
								e.status !== "ISSUED" && /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => E(e.documentId, e.revision),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 text-white font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, F.jsx)(zi, { size: 15 }), " Phát hành"]
								}),
								e.status === "ISSUED" && /* @__PURE__ */ (0, F.jsx)(H, {
									tone: "green",
									size: "sm",
									children: "ISSUED — bất biến"
								})
							]
						}, e.id))
					})]
				})]
			}),
			r === "lo-lien-ket" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsxs)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3",
						children: [/* @__PURE__ */ (0, F.jsx)(di, {
							size: 19,
							className: "text-[#1e5aa8]"
						}), " Lô hàng liên kết"]
					}), u.linkedShipments.length === 0 ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Chưa liên kết lô nào."
					}) : /* @__PURE__ */ (0, F.jsx)("div", {
						className: "space-y-2",
						children: u.linkedShipments.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: "w-9 h-9 rounded-lg bg-blue-100 text-blue-700 grid place-items-center",
									children: /* @__PURE__ */ (0, F.jsx)(Ci, { size: 18 })
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex-1 min-w-0",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-bold text-[14.5px] text-[#0f2a4a]",
										children: e.id
									}), /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											e.customer,
											" · ",
											e.status
										]
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)(P, {
									to: e.to,
									className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
									children: ["MỞ ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 15 })]
								})
							]
						}, e.id))
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
						children: "Liên kết lô mới"
					}), ee.length === 0 ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Tất cả lô đã được liên kết."
					}) : /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3",
						children: [/* @__PURE__ */ (0, F.jsx)(U, {
							label: "Chọn lô hàng",
							required: !0,
							children: /* @__PURE__ */ (0, F.jsxs)("select", {
								value: h,
								onChange: (e) => g(e.target.value),
								className: W(h ? "ok" : "missing"),
								children: [/* @__PURE__ */ (0, F.jsx)("option", {
									value: "",
									children: "-- Chọn lô --"
								}), ee.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
									value: e.id,
									children: [
										e.id,
										" · ",
										e.customer
									]
								}, e.id))]
							})
						}), /* @__PURE__ */ (0, F.jsx)(ba, {
							onClick: D,
							className: "w-full",
							children: "🔗 LIÊN KẾT LÔ"
						})]
					})]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/NewContract.tsx
function ro() {
	let { customers: e, dispatch: t, toast: n } = Xn(), r = xt(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)("HDMB"), [u, d] = (0, _.useState)("");
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[760px]",
		children: [/* @__PURE__ */ (0, F.jsxs)("button", {
			onClick: () => r(-1),
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, F.jsx)(pr, { size: 17 }), " Quay lại"]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-6",
			children: [
				/* @__PURE__ */ (0, F.jsx)(ya, {
					icon: /* @__PURE__ */ (0, F.jsx)(ti, { size: 18 }),
					title: "Tạo hợp đồng mới",
					sub: "HDMB / HDNT + Phụ lục — sau khi tạo sẽ nhập hàng hóa, sinh chứng từ và liên kết lô"
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid sm:grid-cols-2 gap-3",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						label: "Số hợp đồng",
						required: !0,
						error: i ? void 0 : "Nhập số hợp đồng",
						children: /* @__PURE__ */ (0, F.jsx)("input", {
							value: i,
							onChange: (e) => a(e.target.value),
							placeholder: "VD: HDMB-0310",
							className: W(i ? "ok" : "missing")
						})
					}), /* @__PURE__ */ (0, F.jsx)(U, {
						label: "Loại hợp đồng",
						required: !0,
						children: /* @__PURE__ */ (0, F.jsxs)("select", {
							value: c,
							onChange: (e) => l(e.target.value),
							className: W(),
							children: [
								/* @__PURE__ */ (0, F.jsx)("option", {
									value: "HDMB",
									children: "HDMB — Hợp đồng mua bán (≥ 50 triệu)"
								}),
								/* @__PURE__ */ (0, F.jsx)("option", {
									value: "HDNT",
									children: "HDNT — Hợp đồng nguyên tắc (< 50 triệu)"
								}),
								/* @__PURE__ */ (0, F.jsx)("option", {
									value: "PL",
									children: "PL — Phụ lục hợp đồng"
								})
							]
						})
					})]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid gap-3 mt-3",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						label: "Khách hàng / đối tác",
						required: !0,
						error: o ? void 0 : "Chọn khách hàng",
						children: /* @__PURE__ */ (0, F.jsxs)("select", {
							value: o,
							onChange: (e) => s(e.target.value),
							className: W(o ? "ok" : "missing"),
							children: [/* @__PURE__ */ (0, F.jsx)("option", {
								value: "",
								children: "-- Chọn khách --"
							}), e.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
								value: e.id,
								children: [
									e.name,
									" (",
									e.id,
									")"
								]
							}, e.id))]
						})
					}), /* @__PURE__ */ (0, F.jsx)(U, {
						label: "Ghi chú",
						children: /* @__PURE__ */ (0, F.jsx)("input", {
							value: u,
							onChange: (e) => d(e.target.value),
							placeholder: "Ghi chú nội bộ",
							className: W()
						})
					})]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid grid-cols-2 gap-2.5 mt-5",
					children: [/* @__PURE__ */ (0, F.jsx)(Sa, {
						onClick: () => r(-1),
						children: "Hủy"
					}), /* @__PURE__ */ (0, F.jsx)(ba, {
						onClick: () => {
							let e = i.trim().toUpperCase();
							if (!e) {
								n("Thiếu số hợp đồng", "Nhập số hợp đồng (VD: HDMB-0310).", "red");
								return;
							}
							if (!o) {
								n("Chưa chọn khách hàng", "Chọn khách hàng / đối tác cho hợp đồng.", "red");
								return;
							}
							t("contract_create", {
								id: e,
								customerId: o,
								kind: c,
								note: u.trim()
							}) ? (n("Đã gửi tạo hợp đồng " + e, "Backend ghi + audit; tiếp tục nhập hàng hóa & sinh chứng từ.", "green"), r("/hop-dong/" + e)) : n("Không gửi được", "Component chưa kết nối backend.", "red");
						},
						children: "💾 TẠO HỢP ĐỒNG"
					})]
				})
			]
		})]
	});
}
//#endregion
//#region src/pages/PhaseB.tsx
var io = {
	"/khach-hang": "Khách Hàng",
	"/ngu-canh-doi-tac": "Ngữ cảnh Đối tác",
	"/kinh-doanh-bao-gia": "Kinh doanh · Báo giá",
	"/thoa-thuan-ban-giao": "Thòa thuận mua bán",
	"/hop-dong": "Hợp đồng",
	"/hop-dong/moi": "Tạo hợp đồng mới",
	"/tai-chinh/thu-tien": "Thu tiền",
	"/tai-chinh/doi-soat": "Đối soát",
	"/tai-chinh/cong-no-doi-tac": "Công nợ đối tác",
	"/bao-cao-ceo": "Báo cáo CEO",
	"/tra-cuu-thue": "Tra cứu thuế / HS",
	"/so-tay": "Sổ tay",
	"/dich-thuat": "Dịch thuật",
	"/nguoi-dung": "Người dùng & Vai trò"
};
function ao() {
	let { pathname: e } = vt(), t = io[e] ?? "Màn hình phụ";
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "max-w-[680px] mx-auto mt-8",
		children: /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-3xl bg-white border border-slate-200 p-8 text-center anim-slide-up",
			children: [
				/* @__PURE__ */ (0, F.jsx)("span", {
					className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
					children: /* @__PURE__ */ (0, F.jsx)(Vr, { size: 26 })
				}),
				/* @__PURE__ */ (0, F.jsx)("h2", {
					className: "text-[20px] font-extrabold text-[#0f2a4a] mt-4",
					children: t
				}),
				/* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[14.5px] text-slate-500 mt-2 leading-relaxed",
					children: "Màn hình này chưa triển khai. Phần vận hành cốt lõi — Tổng Quan, Việc Cần Xử Lý, Lô Hàng, Chi tiết lô hàng, Tạo Lô Mới và Theo Dõi — đã chạy trên dữ liệu Logistics thật."
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex flex-wrap justify-center gap-2.5 mt-5",
					children: [/* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/",
						className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px]",
						children: ["Về Tổng Quan ", /* @__PURE__ */ (0, F.jsx)(hr, { size: 17 })]
					}), /* @__PURE__ */ (0, F.jsx)(P, {
						to: "/lo-hang",
						className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]",
						children: "Xem Lô Hàng"
					})]
				})
			]
		})
	});
}
//#endregion
//#region src/App.tsx
function oo() {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "min-h-[40vh] grid place-items-center",
		children: /* @__PURE__ */ (0, F.jsx)("p", {
			className: "text-[15px] font-semibold text-slate-500",
			children: "Đang tải dữ liệu vận hành…"
		})
	});
}
function so() {
	let e = (0, _.useSyncExternalStore)(C, S, S);
	return /* @__PURE__ */ (0, F.jsx)(Yn, { children: /* @__PURE__ */ (0, F.jsx)(Gt, { children: /* @__PURE__ */ (0, F.jsx)(Da, { children: e ? /* @__PURE__ */ (0, F.jsxs)(Jt, { children: [
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/",
			element: /* @__PURE__ */ (0, F.jsx)(Aa, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/viec-can-xu-ly",
			element: /* @__PURE__ */ (0, F.jsx)(Ma, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/lo-hang",
			element: /* @__PURE__ */ (0, F.jsx)(Na, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/lo-hang/:id",
			element: /* @__PURE__ */ (0, F.jsx)(Fa, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/tao-lo-moi",
			element: /* @__PURE__ */ (0, F.jsx)(Ia, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/theo-doi",
			element: /* @__PURE__ */ (0, F.jsx)(La, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/khach-hang",
			element: /* @__PURE__ */ (0, F.jsx)(za, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/kinh-doanh-bao-gia",
			element: /* @__PURE__ */ (0, F.jsx)(Ga, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/thoa-thuan-ban-giao",
			element: /* @__PURE__ */ (0, F.jsx)(Xa, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/hop-dong",
			element: /* @__PURE__ */ (0, F.jsx)(Za, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/hop-dong/moi",
			element: /* @__PURE__ */ (0, F.jsx)(ro, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "/hop-dong/:id",
			element: /* @__PURE__ */ (0, F.jsx)(no, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(Kt, {
			path: "*",
			element: /* @__PURE__ */ (0, F.jsx)(ao, {})
		})
	] }) : /* @__PURE__ */ (0, F.jsx)(oo, {}) }) }) });
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/typeof.js
function G(e) {
	"@babel/helpers - typeof";
	return G = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, G(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPrimitive.js
function K(e, t) {
	if (G(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (G(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPropertyKey.js
function co(e) {
	var t = K(e, "string");
	return G(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/defineProperty.js
function lo(e, t, n) {
	return (t = co(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region src/component-entry.tsx
var uo = class extends _.Component {
	constructor(...e) {
		super(...e), lo(this, "state", { error: null });
	}
	static getDerivedStateFromError(e) {
		return { error: e };
	}
	render() {
		return this.state.error ? /* @__PURE__ */ (0, F.jsx)("div", {
			style: {
				padding: 24,
				fontFamily: "inherit"
			},
			children: /* @__PURE__ */ (0, F.jsxs)("div", {
				style: {
					border: "2px solid #fca5a5",
					background: "#fef2f2",
					borderRadius: 16,
					padding: 20,
					textAlign: "center",
					color: "#991b1b"
				},
				children: [/* @__PURE__ */ (0, F.jsx)("p", {
					style: {
						fontWeight: 800,
						fontSize: 16,
						margin: 0
					},
					children: "Logi-good shell gặp lỗi khi render"
				}), /* @__PURE__ */ (0, F.jsxs)("p", {
					style: {
						fontSize: 13.5,
						margin: "8px 0 0",
						opacity: .8
					},
					children: [
						"Nạp lại trang Streamlit để khôi phục. Lỗi:",
						" ",
						String(this.state.error)
					]
				})]
			})
		}) : this.props.children;
	}
}, fo = null, po = null;
function mo(e) {
	return po && e.contains(po) ? po : (po = document.createElement("div"), po.className = "logi-shell", e.appendChild(po), po);
}
function ho(e) {
	O(e.setTriggerValue ?? null);
	let t = mo(e.parentElement);
	return fo || (fo = (0, v.createRoot)(t), fo.render(/* @__PURE__ */ (0, F.jsx)(uo, { children: /* @__PURE__ */ (0, F.jsx)(so, {}) }))), e.data && typeof e.data == "object" && x(e.data), () => {
		try {
			fo?.unmount();
		} catch {}
		fo = null;
		try {
			po?.remove();
		} catch {}
		po = null, O(null);
	};
}
//#endregion
export { ho as default };
