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
	function ee(e, n, r) {
		var i = r.ref;
		return {
			$$typeof: t,
			type: e,
			key: n,
			ref: i === void 0 ? null : i,
			props: r
		};
	}
	function E(e, t) {
		return ee(e.type, t, e.props);
	}
	function D(e) {
		return typeof e == "object" && !!e && e.$$typeof === t;
	}
	function O(e) {
		var t = {
			"=": "=0",
			":": "=2"
		};
		return "$" + e.replace(/[=:]/g, function(e) {
			return t[e];
		});
	}
	var te = /\/+/g;
	function k(e, t) {
		return typeof e == "object" && e && e.key != null ? O("" + e.key) : t.toString(36);
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
		if (c) return o = o(e), c = a === "" ? "." + k(e, 0) : a, S(o) ? (i = "", c != null && (i = c.replace(te, "$&/") + "/"), re(o, r, i, "", function(e) {
			return e;
		})) : o != null && (D(o) && (o = E(o, i + (o.key == null || e && e.key === o.key ? "" : ("" + o.key).replace(te, "$&/") + "/") + c)), r.push(o)), 1;
		c = 0;
		var l = a === "" ? "." : a + ":";
		if (S(e)) for (var u = 0; u < e.length; u++) a = e[u], s = l + k(a, u), c += re(a, r, i, s, o);
		else if (u = m(e), typeof u == "function") for (e = u.call(e), u = 0; !(a = e.next()).done;) a = a.value, s = l + k(a, u++), c += re(a, r, i, s, o);
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
	function ae(e) {
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
	var A = typeof reportError == "function" ? reportError : function(e) {
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
	}, j = {
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
			if (!D(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	};
	e.Activity = f, e.Children = j, e.Component = v, e.Fragment = r, e.Profiler = a, e.PureComponent = b, e.StrictMode = i, e.Suspense = l, e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = w, e.__COMPILER_RUNTIME = {
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
		return ee(e.type, i, r);
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
		return ee(e, a, i);
	}, e.createRef = function() {
		return { current: null };
	}, e.forwardRef = function(e) {
		return {
			$$typeof: c,
			render: e
		};
	}, e.isValidElement = D, e.lazy = function(e) {
		return {
			$$typeof: d,
			_payload: {
				_status: -1,
				_result: e
			},
			_init: ae
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
			i !== null && i(n, r), typeof r == "object" && r && typeof r.then == "function" && r.then(C, A);
		} catch (e) {
			A(e);
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
			if (n(c) !== null) m = !0, S || (S = !0, D());
			else {
				var t = n(l);
				t !== null && k(x, t.startTime - e);
			}
		}
	}
	var S = !1, C = -1, w = 5, T = -1;
	function ee() {
		return g ? !0 : !(e.unstable_now() - T < w);
	}
	function E() {
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
							for (b(t), d = n(c); d !== null && !(d.expirationTime > t && ee());) {
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
								u !== null && k(x, u.startTime - t), i = !1;
							}
						}
						break a;
					} finally {
						d = null, f = a, p = !1;
					}
					i = void 0;
				}
			} finally {
				i ? D() : S = !1;
			}
		}
	}
	var D;
	if (typeof y == "function") D = function() {
		y(E);
	};
	else if (typeof MessageChannel < "u") {
		var O = new MessageChannel(), te = O.port2;
		O.port1.onmessage = E, D = function() {
			te.postMessage(null);
		};
	} else D = function() {
		_(E, 0);
	};
	function k(t, n) {
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
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (v(C), C = -1) : h = !0, k(x, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, S || (S = !0, D()))), r;
	}, e.unstable_shouldYield = ee, e.unstable_wrapCallback = function(e) {
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
	var h = Object.assign, g = Symbol.for("react.element"), _ = Symbol.for("react.transitional.element"), v = Symbol.for("react.portal"), y = Symbol.for("react.fragment"), b = Symbol.for("react.strict_mode"), x = Symbol.for("react.profiler"), S = Symbol.for("react.consumer"), C = Symbol.for("react.context"), w = Symbol.for("react.forward_ref"), T = Symbol.for("react.suspense"), ee = Symbol.for("react.suspense_list"), E = Symbol.for("react.memo"), D = Symbol.for("react.lazy"), O = Symbol.for("react.activity"), te = Symbol.for("react.memo_cache_sentinel"), k = Symbol.iterator;
	function ne(e) {
		return typeof e != "object" || !e ? null : (e = k && e[k] || e["@@iterator"], typeof e == "function" ? e : null);
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
			case ee: return "SuspenseList";
			case O: return "Activity";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case v: return "Portal";
			case C: return e.displayName || "Context";
			case S: return (e._context.displayName || "Context") + ".Consumer";
			case w:
				var t = e.render;
				return e = e.displayName, e || (e = t.displayName || t.name || "", e = e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case E: return t = e.displayName || null, t === null ? ie(e.type) || "Memo" : t;
			case D:
				t = e._payload, e = e._init;
				try {
					return ie(e(t));
				} catch {}
		}
		return null;
	}
	var ae = Array.isArray, A = n.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, j = r.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, oe = {
		pending: !1,
		data: null,
		method: null,
		action: null
	}, se = [], ce = -1;
	function le(e) {
		return { current: e };
	}
	function ue(e) {
		0 > ce || (e.current = se[ce], se[ce] = null, ce--);
	}
	function M(e, t) {
		ce++, se[ce] = e.current, e.current = t;
	}
	var de = le(null), fe = le(null), pe = le(null), me = le(null);
	function he(e, t) {
		switch (M(pe, t), M(fe, e), M(de, null), t.nodeType) {
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
		ue(de), M(de, e);
	}
	function ge() {
		ue(de), ue(fe), ue(pe);
	}
	function _e(e) {
		e.memoizedState !== null && M(me, e);
		var t = de.current, n = Hd(t, e.type);
		t !== n && (M(fe, e), M(de, n));
	}
	function ve(e) {
		fe.current === e && (ue(de), ue(fe)), me.current === e && (ue(me), Qf._currentValue = oe);
	}
	var ye, be;
	function xe(e) {
		if (ye === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			ye = t && t[1] || "", be = -1 < e.stack.indexOf("\n    at") ? " (<anonymous>)" : -1 < e.stack.indexOf("@") ? "@unknown:0:0" : "";
		}
		return "\n" + ye + e + be;
	}
	var Se = !1;
	function Ce(e, t) {
		if (!e || Se) return "";
		Se = !0;
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
			Se = !1, Error.prepareStackTrace = n;
		}
		return (n = e ? e.displayName || e.name : "") ? xe(n) : "";
	}
	function we(e, t) {
		switch (e.tag) {
			case 26:
			case 27:
			case 5: return xe(e.type);
			case 16: return xe("Lazy");
			case 13: return e.child !== t && t !== null ? xe("Suspense Fallback") : xe("Suspense");
			case 19: return xe("SuspenseList");
			case 0:
			case 15: return Ce(e.type, !1);
			case 11: return Ce(e.type.render, !1);
			case 1: return Ce(e.type, !0);
			case 31: return xe("Activity");
			default: return "";
		}
	}
	function Te(e) {
		try {
			var t = "", n = null;
			do
				t += we(e, n), n = e, e = e.return;
			while (e);
			return t;
		} catch (e) {
			return "\nError generating stack: " + e.message + "\n" + e.stack;
		}
	}
	var Ee = Object.prototype.hasOwnProperty, De = t.unstable_scheduleCallback, Oe = t.unstable_cancelCallback, ke = t.unstable_shouldYield, Ae = t.unstable_requestPaint, je = t.unstable_now, Me = t.unstable_getCurrentPriorityLevel, Ne = t.unstable_ImmediatePriority, Pe = t.unstable_UserBlockingPriority, Fe = t.unstable_NormalPriority, Ie = t.unstable_LowPriority, Le = t.unstable_IdlePriority, Re = t.log, ze = t.unstable_setDisableYieldValue, Be = null, Ve = null;
	function He(e) {
		if (typeof Re == "function" && ze(e), Ve && typeof Ve.setStrictMode == "function") try {
			Ve.setStrictMode(Be, e);
		} catch {}
	}
	var Ue = Math.clz32 ? Math.clz32 : Ke, We = Math.log, Ge = Math.LN2;
	function Ke(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (We(e) / Ge | 0) | 0;
	}
	var qe = 256, Je = 262144, Ye = 4194304;
	function Xe(e) {
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
	function Ze(e, t, n) {
		var r = e.pendingLanes;
		if (r === 0) return 0;
		var i = 0, a = e.suspendedLanes, o = e.pingedLanes;
		e = e.warmLanes;
		var s = r & 134217727;
		return s === 0 ? (s = r & ~a, s === 0 ? o === 0 ? n || (n = r & ~e, n !== 0 && (i = Xe(n))) : i = Xe(o) : i = Xe(s)) : (r = s & ~a, r === 0 ? (o &= s, o === 0 ? n || (n = s & ~e, n !== 0 && (i = Xe(n))) : i = Xe(o)) : i = Xe(r)), i === 0 ? 0 : t !== 0 && t !== i && (t & a) === 0 && (a = i & -i, n = t & -t, a >= n || a === 32 && n & 4194048) ? t : i;
	}
	function Qe(e, t) {
		return (e.pendingLanes & ~(e.suspendedLanes & ~e.pingedLanes) & t) === 0;
	}
	function $e(e, t) {
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
	function et() {
		var e = Ye;
		return Ye <<= 1, !(Ye & 62914560) && (Ye = 4194304), e;
	}
	function tt(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function nt(e, t) {
		e.pendingLanes |= t, t !== 268435456 && (e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0);
	}
	function rt(e, t, n, r, i, a) {
		var o = e.pendingLanes;
		e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0, e.expiredLanes &= n, e.entangledLanes &= n, e.errorRecoveryDisabledLanes &= n, e.shellSuspendCounter = 0;
		var s = e.entanglements, c = e.expirationTimes, l = e.hiddenUpdates;
		for (n = o & ~n; 0 < n;) {
			var u = 31 - Ue(n), d = 1 << u;
			s[u] = 0, c[u] = -1;
			var f = l[u];
			if (f !== null) for (l[u] = null, u = 0; u < f.length; u++) {
				var p = f[u];
				p !== null && (p.lane &= -536870913);
			}
			n &= ~d;
		}
		r !== 0 && it(e, r, 0), a !== 0 && i === 0 && e.tag !== 0 && (e.suspendedLanes |= a & ~(o & ~t));
	}
	function it(e, t, n) {
		e.pendingLanes |= t, e.suspendedLanes &= ~t;
		var r = 31 - Ue(t);
		e.entangledLanes |= t, e.entanglements[r] = e.entanglements[r] | 1073741824 | n & 261930;
	}
	function at(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - Ue(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	function ot(e, t) {
		var n = t & -t;
		return n = n & 42 ? 1 : st(n), (n & (e.suspendedLanes | t)) === 0 ? n : 0;
	}
	function st(e) {
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
	function ct(e) {
		return e &= -e, 2 < e ? 8 < e ? e & 134217727 ? 32 : 268435456 : 8 : 2;
	}
	function lt() {
		var e = j.p;
		return e === 0 ? (e = window.event, e === void 0 ? 32 : mp(e.type)) : e;
	}
	function ut(e, t) {
		var n = j.p;
		try {
			return j.p = e, t();
		} finally {
			j.p = n;
		}
	}
	var dt = Math.random().toString(36).slice(2), ft = "__reactFiber$" + dt, pt = "__reactProps$" + dt, mt = "__reactContainer$" + dt, ht = "__reactEvents$" + dt, gt = "__reactListeners$" + dt, _t = "__reactHandles$" + dt, vt = "__reactResources$" + dt, yt = "__reactMarker$" + dt;
	function bt(e) {
		delete e[ft], delete e[pt], delete e[ht], delete e[gt], delete e[_t];
	}
	function xt(e) {
		var t = e[ft];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[mt] || n[ft]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = df(e); e !== null;) {
					if (n = e[ft]) return n;
					e = df(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function St(e) {
		if (e = e[ft] || e[mt]) {
			var t = e.tag;
			if (t === 5 || t === 6 || t === 13 || t === 31 || t === 26 || t === 27 || t === 3) return e;
		}
		return null;
	}
	function Ct(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e.stateNode;
		throw Error(i(33));
	}
	function wt(e) {
		var t = e[vt];
		return t || (t = e[vt] = {
			hoistableStyles: /* @__PURE__ */ new Map(),
			hoistableScripts: /* @__PURE__ */ new Map()
		}), t;
	}
	function Tt(e) {
		e[yt] = !0;
	}
	var Et = /* @__PURE__ */ new Set(), Dt = {};
	function Ot(e, t) {
		kt(e, t), kt(e + "Capture", t);
	}
	function kt(e, t) {
		for (Dt[e] = t, e = 0; e < t.length; e++) Et.add(t[e]);
	}
	var At = RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"), jt = {}, Mt = {};
	function Nt(e) {
		return Ee.call(Mt, e) ? !0 : Ee.call(jt, e) ? !1 : At.test(e) ? Mt[e] = !0 : (jt[e] = !0, !1);
	}
	function Pt(e, t, n) {
		if (Nt(t)) {
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
	function Ft(e, t, n) {
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
	function It(e, t, n, r) {
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
	function Lt(e) {
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
	function Rt(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function zt(e, t, n) {
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
	function Bt(e) {
		if (!e._valueTracker) {
			var t = Rt(e) ? "checked" : "value";
			e._valueTracker = zt(e, t, "" + e[t]);
		}
	}
	function Vt(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = Rt(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== n && (t.setValue(e), !0);
	}
	function Ht(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch {
			return e.body;
		}
	}
	var Ut = /[\n"\\]/g;
	function Wt(e) {
		return e.replace(Ut, function(e) {
			return "\\" + e.charCodeAt(0).toString(16) + " ";
		});
	}
	function Gt(e, t, n, r, i, a, o, s) {
		e.name = "", o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" ? e.type = o : e.removeAttribute("type"), t == null ? o !== "submit" && o !== "reset" || e.removeAttribute("value") : o === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + Lt(t)) : e.value !== "" + Lt(t) && (e.value = "" + Lt(t)), t == null ? n == null ? r != null && e.removeAttribute("value") : qt(e, o, Lt(n)) : qt(e, o, Lt(t)), i == null && a != null && (e.defaultChecked = !!a), i != null && (e.checked = i && typeof i != "function" && typeof i != "symbol"), s != null && typeof s != "function" && typeof s != "symbol" && typeof s != "boolean" ? e.name = "" + Lt(s) : e.removeAttribute("name");
	}
	function Kt(e, t, n, r, i, a, o, s) {
		if (a != null && typeof a != "function" && typeof a != "symbol" && typeof a != "boolean" && (e.type = a), t != null || n != null) {
			if (!(a !== "submit" && a !== "reset" || t != null)) {
				Bt(e);
				return;
			}
			n = n == null ? "" : "" + Lt(n), t = t == null ? n : "" + Lt(t), s || t === e.value || (e.value = t), e.defaultValue = t;
		}
		r = r ?? i, r = typeof r != "function" && typeof r != "symbol" && !!r, e.checked = s ? e.checked : !!r, e.defaultChecked = !!r, o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" && (e.name = o), Bt(e);
	}
	function qt(e, t, n) {
		t === "number" && Ht(e.ownerDocument) === e || e.defaultValue === "" + n || (e.defaultValue = "" + n);
	}
	function N(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + Lt(n), t = null, i = 0; i < e.length; i++) {
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
		if (t != null && (t = "" + Lt(t), t !== e.value && (e.value = t), n == null)) {
			e.defaultValue !== t && (e.defaultValue = t);
			return;
		}
		e.defaultValue = n == null ? "" : "" + Lt(n);
	}
	function Yt(e, t, n, r) {
		if (t == null) {
			if (r != null) {
				if (n != null) throw Error(i(92));
				if (ae(r)) {
					if (1 < r.length) throw Error(i(93));
					r = r[0];
				}
				n = r;
			}
			n ?? (n = ""), t = n;
		}
		n = Lt(t), e.defaultValue = n, r = e.textContent, r === n && r !== "" && r !== null && (e.value = r), Bt(e);
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
		var t = St(e);
		if (t && (e = t.stateNode)) {
			var n = e[pt] || null;
			a: switch (e = t.stateNode, t.type) {
				case "input":
					if (Gt(e, n.value, n.defaultValue, n.defaultValue, n.checked, n.defaultChecked, n.type, n.name), t = n.name, n.type === "radio" && t != null) {
						for (n = e; n.parentNode;) n = n.parentNode;
						for (n = n.querySelectorAll("input[name=\"" + Wt("" + t) + "\"][type=\"radio\"]"), t = 0; t < n.length; t++) {
							var r = n[t];
							if (r !== e && r.form === e.form) {
								var a = r[pt] || null;
								if (!a) throw Error(i(90));
								Gt(r, a.value, a.defaultValue, a.defaultValue, a.checked, a.defaultChecked, a.type, a.name);
							}
						}
						for (t = 0; t < n.length; t++) r = n[t], r.form === e.form && Vt(r);
					}
					break a;
				case "textarea":
					Jt(e, n.value, n.defaultValue);
					break a;
				case "select": t = n.value, t != null && N(e, !!n.multiple, t, !1);
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
			if (dn = !1, (cn !== null || ln !== null) && (yu(), cn && (t = cn, e = ln, ln = cn = null, un(t), e))) for (t = 0; t < e.length; t++) un(e[t]);
		}
	}
	function pn(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var r = n[pt] || null;
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
	}), Nn = wn(Mn), Pn = wn(h({}, Mn, { dataTransfer: 0 })), Fn = wn(h({}, Dn, { relatedTarget: 0 })), P = wn(h({}, Tn, {
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
	})), qn = wn(h({}, Mn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), F = wn(h({}, Tn, {
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
		cn ? ln ? ln.push(r) : ln = [r] : cn = r, t = Td(t, "onChange"), 0 < t.length && (n = new En("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var lr = null, ur = null;
	function I(e) {
		vd(e, 0);
	}
	function dr(e) {
		if (Vt(Ct(e))) return e;
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
		lr && (lr.detachEvent("onpropertychange", vr), ur = lr = null);
	}
	function vr(e) {
		if (e.propertyName === "value" && dr(ur)) {
			var t = [];
			cr(t, ur, e, sn(e)), fn(I, t);
		}
	}
	function yr(e, t, n) {
		e === "focusin" ? (_r(), lr = t, ur = n, lr.attachEvent("onpropertychange", vr)) : e === "focusout" && _r();
	}
	function br(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return dr(ur);
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
			if (!Ee.call(t, i) || !wr(e[i], t[i])) return !1;
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
		for (var t = Ht(e.document); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = Ht(e.document);
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
		Fr || Mr == null || Mr !== Ht(r) || (r = Mr, "selectionStart" in r && Ar(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Pr && Tr(Pr, r) || (Pr = r, r = Td(Nr, "onSelect"), 0 < r.length && (t = new En("onSelect", "select", null, t, n), e.push({
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
		Yr.set(e, t), Ot(t, [e]);
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
		return e.tag === 3 ? (a = e.stateNode, i && t !== null && (i = 31 - Ue(n), e = a.hiddenUpdates, r = e[i], r === null ? e[i] = [t] : r.push(t), t.lane = n | 536870912), a) : null;
	}
	function si(e) {
		if (50 < uu) throw uu = 0, du = null, Error(i(185));
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
		else if (typeof e == "string") s = Uf(e, n, de.current) ? 26 : e === "html" || e === "head" || e === "body" ? 27 : 5;
		else a: switch (e) {
			case O: return e = ui(31, n, t, a), e.elementType = O, e.lanes = o, e;
			case y: return hi(n.children, a, o, t);
			case b:
				s = 8, a |= 24;
				break;
			case x: return e = ui(12, n, t, a | 2), e.elementType = x, e.lanes = o, e;
			case T: return e = ui(13, n, t, a), e.elementType = T, e.lanes = o, e;
			case ee: return e = ui(19, n, t, a), e.elementType = ee, e.lanes = o, e;
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
					case E:
						s = 14;
						break a;
					case D:
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
				stack: Te(t)
			}, yi.set(e, t), t) : n;
		}
		return {
			value: e,
			source: t,
			stack: Te(t)
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
		var i = 32 - Ue(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - Ue(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, Oi = 1 << 32 - Ue(t) + i | n << i | r, ki = a + e;
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
	var Fi = null, Ii = null, L = !1, Li = null, Ri = !1, zi = Error(i(519));
	function Bi(e) {
		throw Ki(bi(Error(i(418, 1 < arguments.length && arguments[1] !== void 0 && arguments[1] ? "text" : "HTML", "")), e)), zi;
	}
	function Vi(e) {
		var t = e.stateNode, n = e.type, r = e.memoizedProps;
		switch (t[ft] = e, t[pt] = r, n) {
			case "dialog":
				$("cancel", t), $("close", t);
				break;
			case "iframe":
			case "object":
			case "embed":
				$("load", t);
				break;
			case "video":
			case "audio":
				for (n = 0; n < gd.length; n++) $(gd[n], t);
				break;
			case "source":
				$("error", t);
				break;
			case "img":
			case "image":
			case "link":
				$("error", t), $("load", t);
				break;
			case "details":
				$("toggle", t);
				break;
			case "input":
				$("invalid", t), Kt(t, r.value, r.defaultValue, r.checked, r.defaultChecked, r.type, r.name, !0);
				break;
			case "select":
				$("invalid", t);
				break;
			case "textarea": $("invalid", t), Yt(t, r.value, r.defaultValue, r.children);
		}
		n = r.children, typeof n != "string" && typeof n != "number" && typeof n != "bigint" || t.textContent === "" + n || !0 === r.suppressHydrationWarning || jd(t.textContent, n) ? (r.popover != null && ($("beforetoggle", t), $("toggle", t)), r.onScroll != null && $("scroll", t), r.onScrollEnd != null && $("scrollend", t), r.onClick != null && (t.onclick = an), t = !0) : t = !1, t || Bi(e, !0);
	}
	function Hi(e) {
		for (Fi = e.return; Fi;) switch (Fi.tag) {
			case 5:
			case 31:
			case 13:
				Ri = !1;
				return;
			case 27:
			case 3:
				Ri = !0;
				return;
			default: Fi = Fi.return;
		}
	}
	function Ui(e) {
		if (e !== Fi) return !1;
		if (!L) return Hi(e), L = !0, !1;
		var t = e.tag, n;
		if ((n = t !== 3 && t !== 27) && ((n = t === 5) && (n = e.type, n = n === "form" || n === "button" || Ud(e.type, e.memoizedProps)), n = !n), n && Ii && Bi(e), Hi(e), t === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			Ii = uf(e);
		} else if (t === 31) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			Ii = uf(e);
		} else t === 27 ? (t = Ii, Zd(e.type) ? (e = lf, lf = null, Ii = e) : Ii = t) : Ii = Fi ? cf(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Wi() {
		Ii = Fi = null, L = !1;
	}
	function Gi() {
		var e = Li;
		return e !== null && (Xl === null ? Xl = e : Xl.push.apply(Xl, e), Li = null), e;
	}
	function Ki(e) {
		Li === null ? Li = [e] : Li.push(e);
	}
	var qi = le(null), Ji = null, Yi = null;
	function Xi(e, t, n) {
		M(qi, t._currentValue), t._currentValue = n;
	}
	function Zi(e) {
		e._currentValue = qi.current, ue(qi);
	}
	function Qi(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function $i(e, t, n, r) {
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
						o.lanes |= n, c = o.alternate, c !== null && (c.lanes |= n), Qi(o.return, n, e), r || (s = null);
						break a;
					}
					o = c.next;
				}
			} else if (a.tag === 18) {
				if (s = a.return, s === null) throw Error(i(341));
				s.lanes |= n, o = s.alternate, o !== null && (o.lanes |= n), Qi(s, n, e), s = null;
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
	function ea(e, t, n, r) {
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
			} else if (a === me.current) {
				if (s = a.alternate, s === null) throw Error(i(387));
				s.memoizedState.memoizedState !== a.memoizedState.memoizedState && (e === null ? e = [Qf] : e.push(Qf));
			}
			a = a.return;
		}
		e !== null && $i(t, e, n, r), t.flags |= 262144;
	}
	function ta(e) {
		for (e = e.firstContext; e !== null;) {
			if (!wr(e.context._currentValue, e.memoizedValue)) return !0;
			e = e.next;
		}
		return !1;
	}
	function na(e) {
		Ji = e, Yi = null, e = e.dependencies, e !== null && (e.firstContext = null);
	}
	function R(e) {
		return ia(Ji, e);
	}
	function ra(e, t) {
		return Ji === null && na(e), ia(e, t);
	}
	function ia(e, t) {
		var n = t._currentValue;
		if (t = {
			context: t,
			memoizedValue: n,
			next: null
		}, Yi === null) {
			if (e === null) throw Error(i(308));
			Yi = t, e.dependencies = {
				lanes: 0,
				firstContext: t
			}, e.flags |= 524288;
		} else Yi = Yi.next = t;
		return n;
	}
	var aa = typeof AbortController < "u" ? AbortController : function() {
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
	}, oa = t.unstable_scheduleCallback, sa = t.unstable_NormalPriority, ca = {
		$$typeof: C,
		Consumer: null,
		Provider: null,
		_currentValue: null,
		_currentValue2: null,
		_threadCount: 0
	};
	function la() {
		return {
			controller: new aa(),
			data: /* @__PURE__ */ new Map(),
			refCount: 0
		};
	}
	function ua(e) {
		e.refCount--, e.refCount === 0 && oa(sa, function() {
			e.controller.abort();
		});
	}
	var da = null, fa = 0, pa = 0, ma = null;
	function ha(e, t) {
		if (da === null) {
			var n = da = [];
			fa = 0, pa = ud(), ma = {
				status: "pending",
				value: void 0,
				then: function(e) {
					n.push(e);
				}
			};
		}
		return fa++, t.then(ga, ga), t;
	}
	function ga() {
		if (--fa === 0 && da !== null) {
			ma !== null && (ma.status = "fulfilled");
			var e = da;
			da = null, pa = 0, ma = null;
			for (var t = 0; t < e.length; t++) (0, e[t])();
		}
	}
	function _a(e, t) {
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
	var va = A.S;
	A.S = function(e, t) {
		$l = je(), typeof t == "object" && t && typeof t.then == "function" && ha(e, t), va !== null && va(e, t);
	};
	var ya = le(null);
	function ba() {
		var e = ya.current;
		return e === null ? Ll.pooledCache : e;
	}
	function xa(e, t) {
		t === null ? M(ya, ya.current) : M(ya, t.pool);
	}
	function Sa() {
		var e = ba();
		return e === null ? null : {
			parent: ca._currentValue,
			pool: e
		};
	}
	var Ca = Error(i(460)), wa = Error(i(474)), Ta = Error(i(542)), Ea = { then: function() {} };
	function Da(e) {
		return e = e.status, e === "fulfilled" || e === "rejected";
	}
	function Oa(e, t, n) {
		switch (n = e[n], n === void 0 ? e.push(t) : n !== t && (t.then(an, an), t = n), t.status) {
			case "fulfilled": return t.value;
			case "rejected": throw e = t.reason, Ma(e), e;
			default:
				if (typeof t.status == "string") t.then(an, an);
				else {
					if (e = Ll, e !== null && 100 < e.shellSuspendCounter) throw Error(i(482));
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
					case "rejected": throw e = t.reason, Ma(e), e;
				}
				throw Aa = t, Ca;
		}
	}
	function ka(e) {
		try {
			var t = e._init;
			return t(e._payload);
		} catch (e) {
			throw typeof e == "object" && e && typeof e.then == "function" ? (Aa = e, Ca) : e;
		}
	}
	var Aa = null;
	function ja() {
		if (Aa === null) throw Error(i(459));
		var e = Aa;
		return Aa = null, e;
	}
	function Ma(e) {
		if (e === Ca || e === Ta) throw Error(i(483));
	}
	var Na = null, Pa = 0;
	function Fa(e) {
		var t = Pa;
		return Pa += 1, Na === null && (Na = []), Oa(Na, e, t);
	}
	function Ia(e, t) {
		t = t.props.ref, e.ref = t === void 0 ? null : t;
	}
	function La(e, t) {
		throw t.$$typeof === g ? Error(i(525)) : (e = Object.prototype.toString.call(t), Error(i(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e)));
	}
	function Ra(e) {
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
			return i === y ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === D && ka(i) === t.type) ? (t = a(t, n.props), Ia(t, n), t.return = e, t) : (t = mi(n.type, n.key, n.props, null, e.mode, r), Ia(t, n), t.return = e, t);
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
					case _: return n = mi(t.type, t.key, t.props, null, e.mode, n), Ia(n, t), n.return = e, n;
					case v: return t = vi(t, e.mode, n), t.return = e, t;
					case D: return t = ka(t), f(e, t, n);
				}
				if (ae(t) || ne(t)) return t = hi(t, e.mode, n, null), t.return = e, t;
				if (typeof t.then == "function") return f(e, Fa(t), n);
				if (t.$$typeof === C) return f(e, ra(e, t), n);
				La(e, t);
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
					case D: return n = ka(n), p(e, t, n, r);
				}
				if (ae(n) || ne(n)) return i === null ? d(e, t, n, r, null) : null;
				if (typeof n.then == "function") return p(e, t, Fa(n), r);
				if (n.$$typeof === C) return p(e, t, ra(e, n), r);
				La(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number" || typeof r == "bigint") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case _: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case v: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case D: return r = ka(r), m(e, t, n, r, i);
				}
				if (ae(r) || ne(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				if (typeof r.then == "function") return m(e, t, n, Fa(r), i);
				if (r.$$typeof === C) return m(e, t, n, ra(t, r), i);
				La(t, r);
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
			if (h === s.length) return n(i, d), L && Ai(i, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(i, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return L && Ai(i, h), l;
			}
			for (d = r(d); h < s.length; h++) g = m(d, i, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(i, e);
			}), L && Ai(i, h), l;
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
			if (v.done) return n(a, h), L && Ai(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return L && Ai(a, g), u;
			}
			for (h = r(h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), L && Ai(a, g), u;
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
									} else if (r.elementType === l || typeof l == "object" && l && l.$$typeof === D && ka(l) === r.type) {
										n(e, r.sibling), c = a(r, o.props), Ia(c, o), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							o.type === y ? (c = hi(o.props.children, e.mode, c, o.key), c.return = e, e = c) : (c = mi(o.type, o.key, o.props, null, e.mode, c), Ia(c, o), c.return = e, e = c);
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
					case D: return o = ka(o), b(e, r, o, c);
				}
				if (ae(o)) return h(e, r, o, c);
				if (ne(o)) {
					if (l = ne(o), typeof l != "function") throw Error(i(150));
					return o = l.call(o), g(e, r, o, c);
				}
				if (typeof o.then == "function") return b(e, r, Fa(o), c);
				if (o.$$typeof === C) return b(e, r, ra(e, o), c);
				La(e, o);
			}
			return typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint" ? (o = "" + o, r !== null && r.tag === 6 ? (n(e, r.sibling), c = a(r, o), c.return = e, e = c) : (n(e, r), c = gi(o, e.mode, c), c.return = e, e = c), s(e)) : n(e, r);
		}
		return function(e, t, n, r) {
			try {
				Pa = 0;
				var i = b(e, t, n, r);
				return Na = null, i;
			} catch (t) {
				if (t === Ca || t === Ta) throw t;
				var a = ui(29, t, null, e.mode);
				return a.lanes = r, a.return = e, a;
			}
		};
	}
	var za = Ra(!0), z = Ra(!1), Ba = !1;
	function Va(e) {
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
	function Ha(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			callbacks: null
		});
	}
	function B(e) {
		return {
			lane: e,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function Ua(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, J & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, t = si(e), oi(e, null, n), t;
		}
		return ri(e, r, t, n), si(e);
	}
	function Wa(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194048)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, at(e, n);
		}
	}
	function Ga(e, t) {
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
	var Ka = !1;
	function V() {
		if (Ka) {
			var e = ma;
			if (e !== null) throw e;
		}
	}
	function qa(e, t, n, r) {
		Ka = !1;
		var i = e.updateQueue;
		Ba = !1;
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
				if (p ? (X & f) === f : (r & f) === f) {
					f !== 0 && f === pa && (Ka = !0), u !== null && (u = u.next = {
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
							case 2: Ba = !0;
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
			u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, a === null && (i.shared.lanes = 0), Wl |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function Ja(e, t) {
		if (typeof e != "function") throw Error(i(191, e));
		e.call(t);
	}
	function H(e, t) {
		var n = e.callbacks;
		if (n !== null) for (e.callbacks = null, e = 0; e < n.length; e++) Ja(n[e], t);
	}
	var Ya = le(null), U = le(0);
	function W(e, t) {
		e = Hl, M(U, e), M(Ya, t), Hl = e | t.baseLanes;
	}
	function G() {
		M(U, Hl), M(Ya, Ya.current);
	}
	function Xa() {
		Hl = U.current, ue(Ya), ue(U);
	}
	var Za = le(null), Qa = null;
	function $a(e) {
		var t = e.alternate;
		M(io, io.current & 1), M(Za, e), Qa === null && (t === null || Ya.current !== null || t.memoizedState !== null) && (Qa = e);
	}
	function eo(e) {
		M(io, io.current), M(Za, e), Qa === null && (Qa = e);
	}
	function to(e) {
		e.tag === 22 ? (M(io, io.current), M(Za, e), Qa === null && (Qa = e)) : no(e);
	}
	function no() {
		M(io, io.current), M(Za, Za.current);
	}
	function ro(e) {
		ue(Za), Qa === e && (Qa = null), ue(io);
	}
	var io = le(0);
	function ao(e) {
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
	var oo = 0, K = null, q = null, so = null, co = !1, lo = !1, uo = !1, fo = 0, po = 0, mo = null, ho = 0;
	function go() {
		throw Error(i(321));
	}
	function _o(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!wr(e[n], t[n])) return !1;
		return !0;
	}
	function vo(e, t, n, r, i, a) {
		return oo = a, K = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, A.H = e === null || e.memoizedState === null ? Fs : Is, uo = !1, a = n(r, i), uo = !1, lo && (a = bo(t, n, r, i)), yo(e), a;
	}
	function yo(e) {
		A.H = Ps;
		var t = q !== null && q.next !== null;
		if (oo = 0, so = q = K = null, co = !1, po = 0, mo = null, t) throw Error(i(300));
		e === null || $s || (e = e.dependencies, e !== null && ta(e) && ($s = !0));
	}
	function bo(e, t, n, r) {
		K = e;
		var a = 0;
		do {
			if (lo && (mo = null), po = 0, lo = !1, 25 <= a) throw Error(i(301));
			if (a += 1, so = q = null, e.updateQueue != null) {
				var o = e.updateQueue;
				o.lastEffect = null, o.events = null, o.stores = null, o.memoCache != null && (o.memoCache.index = 0);
			}
			A.H = Ls, o = t(n, r);
		} while (lo);
		return o;
	}
	function xo() {
		var e = A.H, t = e.useState()[0];
		return t = typeof t.then == "function" ? Oo(t) : t, e = e.useState()[0], (q === null ? null : q.memoizedState) !== e && (K.flags |= 1024), t;
	}
	function So() {
		var e = fo !== 0;
		return fo = 0, e;
	}
	function Co(e, t, n) {
		t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~n;
	}
	function wo(e) {
		if (co) {
			for (e = e.memoizedState; e !== null;) {
				var t = e.queue;
				t !== null && (t.pending = null), e = e.next;
			}
			co = !1;
		}
		oo = 0, so = q = K = null, lo = !1, po = fo = 0, mo = null;
	}
	function To() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return so === null ? K.memoizedState = so = e : so = so.next = e, so;
	}
	function Eo() {
		if (q === null) {
			var e = K.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = q.next;
		var t = so === null ? K.memoizedState : so.next;
		if (t !== null) so = t, q = e;
		else {
			if (e === null) throw K.alternate === null ? Error(i(467)) : Error(i(310));
			q = e, e = {
				memoizedState: q.memoizedState,
				baseState: q.baseState,
				baseQueue: q.baseQueue,
				queue: q.queue,
				next: null
			}, so === null ? K.memoizedState = so = e : so = so.next = e;
		}
		return so;
	}
	function Do() {
		return {
			lastEffect: null,
			events: null,
			stores: null,
			memoCache: null
		};
	}
	function Oo(e) {
		var t = po;
		return po += 1, mo === null && (mo = []), e = Oa(mo, e, t), t = K, (so === null ? t.memoizedState : so.next) === null && (t = t.alternate, A.H = t === null || t.memoizedState === null ? Fs : Is), e;
	}
	function ko(e) {
		if (typeof e == "object" && e) {
			if (typeof e.then == "function") return Oo(e);
			if (e.$$typeof === C) return R(e);
		}
		throw Error(i(438, String(e)));
	}
	function Ao(e) {
		var t = null, n = K.updateQueue;
		if (n !== null && (t = n.memoCache), t == null) {
			var r = K.alternate;
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
		}), n === null && (n = Do(), K.updateQueue = n), n.memoCache = t, n = t.data[t.index], n === void 0) for (n = t.data[t.index] = Array(e), r = 0; r < e; r++) n[r] = te;
		return t.index++, n;
	}
	function jo(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function Mo(e) {
		return No(Eo(), q, e);
	}
	function No(e, t, n) {
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
				if (f === u.lane ? (oo & f) === f : (X & f) === f) {
					var p = u.revertLane;
					if (p === 0) l !== null && (l = l.next = {
						lane: 0,
						revertLane: 0,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}), f === pa && (d = !0);
					else if ((oo & p) === p) {
						u = u.next, p === pa && (d = !0);
						continue;
					} else f = {
						lane: 0,
						revertLane: u.revertLane,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}, l === null ? (c = l = f, s = o) : l = l.next = f, K.lanes |= p, Wl |= p;
					f = u.action, uo && n(o, f), o = u.hasEagerState ? u.eagerState : n(o, f);
				} else p = {
					lane: f,
					revertLane: u.revertLane,
					gesture: u.gesture,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}, l === null ? (c = l = p, s = o) : l = l.next = p, K.lanes |= f, Wl |= f;
				u = u.next;
			} while (u !== null && u !== t);
			if (l === null ? s = o : l.next = c, !wr(o, e.memoizedState) && ($s = !0, d && (n = ma, n !== null))) throw n;
			e.memoizedState = o, e.baseState = s, e.baseQueue = l, r.lastRenderedState = o;
		}
		return a === null && (r.lanes = 0), [e.memoizedState, r.dispatch];
	}
	function Po(e) {
		var t = Eo(), n = t.queue;
		if (n === null) throw Error(i(311));
		n.lastRenderedReducer = e;
		var r = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			wr(o, t.memoizedState) || ($s = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, r];
	}
	function Fo(e, t, n) {
		var r = K, a = Eo(), o = L;
		if (o) {
			if (n === void 0) throw Error(i(407));
			n = n();
		} else n = t();
		var s = !wr((q || a).memoizedState, n);
		if (s && (a.memoizedState = n, $s = !0), a = a.queue, os(Ro.bind(null, r, a, e), [e]), a.getSnapshot !== t || s || so !== null && so.memoizedState.tag & 1) {
			if (r.flags |= 2048, ts(9, { destroy: void 0 }, Lo.bind(null, r, a, n, t), null), Ll === null) throw Error(i(349));
			o || oo & 127 || Io(r, t, n);
		}
		return n;
	}
	function Io(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = K.updateQueue, t === null ? (t = Do(), K.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function Lo(e, t, n, r) {
		t.value = n, t.getSnapshot = r, zo(t) && Bo(e);
	}
	function Ro(e, t, n) {
		return n(function() {
			zo(t) && Bo(e);
		});
	}
	function zo(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !wr(e, n);
		} catch {
			return !0;
		}
	}
	function Bo(e) {
		var t = ai(e, 2);
		t !== null && mu(t, e, 2);
	}
	function Vo(e) {
		var t = To();
		if (typeof e == "function") {
			var n = e;
			if (e = n(), uo) {
				He(!0);
				try {
					n();
				} finally {
					He(!1);
				}
			}
		}
		return t.memoizedState = t.baseState = e, t.queue = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: jo,
			lastRenderedState: e
		}, t;
	}
	function Ho(e, t, n, r) {
		return e.baseState = n, No(e, q, typeof r == "function" ? r : jo);
	}
	function Uo(e, t, n, r, a) {
		if (js(e)) throw Error(i(485));
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
			A.T === null ? o.isTransition = !1 : n(!0), r(o), n = t.pending, n === null ? (o.next = t.pending = o, Wo(t, o)) : (o.next = n.next, t.pending = n.next = o);
		}
	}
	function Wo(e, t) {
		var n = t.action, r = t.payload, i = e.state;
		if (t.isTransition) {
			var a = A.T, o = {};
			A.T = o;
			try {
				var s = n(i, r), c = A.S;
				c !== null && c(o, s), Go(e, t, s);
			} catch (n) {
				qo(e, t, n);
			} finally {
				a !== null && o.types !== null && (a.types = o.types), A.T = a;
			}
		} else try {
			a = n(i, r), Go(e, t, a);
		} catch (n) {
			qo(e, t, n);
		}
	}
	function Go(e, t, n) {
		typeof n == "object" && n && typeof n.then == "function" ? n.then(function(n) {
			Ko(e, t, n);
		}, function(n) {
			return qo(e, t, n);
		}) : Ko(e, t, n);
	}
	function Ko(e, t, n) {
		t.status = "fulfilled", t.value = n, Jo(t), e.state = n, t = e.pending, t !== null && (n = t.next, n === t ? e.pending = null : (n = n.next, t.next = n, Wo(e, n)));
	}
	function qo(e, t, n) {
		var r = e.pending;
		if (e.pending = null, r !== null) {
			r = r.next;
			do
				t.status = "rejected", t.reason = n, Jo(t), t = t.next;
			while (t !== r);
		}
		e.action = null;
	}
	function Jo(e) {
		e = e.listeners;
		for (var t = 0; t < e.length; t++) (0, e[t])();
	}
	function Yo(e, t) {
		return t;
	}
	function Xo(e, t) {
		if (L) {
			var n = Ll.formState;
			if (n !== null) {
				a: {
					var r = K;
					if (L) {
						if (Ii) {
							b: {
								for (var i = Ii, a = Ri; i.nodeType !== 8;) {
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
								Ii = cf(i.nextSibling), r = i.data === "F!";
								break a;
							}
						}
						Bi(r);
					}
					r = !1;
				}
				r && (t = n[0]);
			}
		}
		return n = To(), n.memoizedState = n.baseState = t, r = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Yo,
			lastRenderedState: t
		}, n.queue = r, n = Os.bind(null, K, r), r.dispatch = n, r = Vo(!1), a = As.bind(null, K, !1, r.queue), r = To(), i = {
			state: t,
			dispatch: null,
			action: e,
			pending: null
		}, r.queue = i, n = Uo.bind(null, K, i, a, n), i.dispatch = n, r.memoizedState = e, [
			t,
			n,
			!1
		];
	}
	function Zo(e) {
		return Qo(Eo(), q, e);
	}
	function Qo(e, t, n) {
		if (t = No(e, t, Yo)[0], e = Mo(jo)[0], typeof t == "object" && t && typeof t.then == "function") try {
			var r = Oo(t);
		} catch (e) {
			throw e === Ca ? Ta : e;
		}
		else r = t;
		t = Eo();
		var i = t.queue, a = i.dispatch;
		return n !== t.memoizedState && (K.flags |= 2048, ts(9, { destroy: void 0 }, $o.bind(null, i, n), null)), [
			r,
			a,
			e
		];
	}
	function $o(e, t) {
		e.action = t;
	}
	function es(e) {
		var t = Eo(), n = q;
		if (n !== null) return Qo(t, n, e);
		Eo(), t = t.memoizedState, n = Eo();
		var r = n.queue.dispatch;
		return n.memoizedState = e, [
			t,
			r,
			!1
		];
	}
	function ts(e, t, n, r) {
		return e = {
			tag: e,
			create: n,
			deps: r,
			inst: t,
			next: null
		}, t = K.updateQueue, t === null && (t = Do(), K.updateQueue = t), n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e), e;
	}
	function ns() {
		return Eo().memoizedState;
	}
	function rs(e, t, n, r) {
		var i = To();
		K.flags |= e, i.memoizedState = ts(1 | t, { destroy: void 0 }, n, r === void 0 ? null : r);
	}
	function is(e, t, n, r) {
		var i = Eo();
		r = r === void 0 ? null : r;
		var a = i.memoizedState.inst;
		q !== null && r !== null && _o(r, q.memoizedState.deps) ? i.memoizedState = ts(t, a, n, r) : (K.flags |= e, i.memoizedState = ts(1 | t, a, n, r));
	}
	function as(e, t) {
		rs(8390656, 8, e, t);
	}
	function os(e, t) {
		is(2048, 8, e, t);
	}
	function ss(e) {
		K.flags |= 4;
		var t = K.updateQueue;
		if (t === null) t = Do(), K.updateQueue = t, t.events = [e];
		else {
			var n = t.events;
			n === null ? t.events = [e] : n.push(e);
		}
	}
	function cs(e) {
		var t = Eo().memoizedState;
		return ss({
			ref: t,
			nextImpl: e
		}), function() {
			if (J & 2) throw Error(i(440));
			return t.impl.apply(void 0, arguments);
		};
	}
	function ls(e, t) {
		return is(4, 2, e, t);
	}
	function us(e, t) {
		return is(4, 4, e, t);
	}
	function ds(e, t) {
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
	function fs(e, t, n) {
		n = n == null ? null : n.concat([e]), is(4, 4, ds.bind(null, t, e), n);
	}
	function ps() {}
	function ms(e, t) {
		var n = Eo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return t !== null && _o(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function hs(e, t) {
		var n = Eo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		if (t !== null && _o(t, r[1])) return r[0];
		if (r = e(), uo) {
			He(!0);
			try {
				e();
			} finally {
				He(!1);
			}
		}
		return n.memoizedState = [r, t], r;
	}
	function gs(e, t, n) {
		return n === void 0 || oo & 1073741824 && !(X & 261930) ? e.memoizedState = t : (e.memoizedState = n, e = pu(), K.lanes |= e, Wl |= e, n);
	}
	function _s(e, t, n, r) {
		return wr(n, t) ? n : Ya.current === null ? !(oo & 42) || oo & 1073741824 && !(X & 261930) ? ($s = !0, e.memoizedState = n) : (e = pu(), K.lanes |= e, Wl |= e, t) : (e = gs(e, n, r), wr(e, t) || ($s = !0), e);
	}
	function vs(e, t, n, r, i) {
		var a = j.p;
		j.p = a !== 0 && 8 > a ? a : 8;
		var o = A.T, s = {};
		A.T = s, As(e, !1, t, n);
		try {
			var c = i(), l = A.S;
			l !== null && l(s, c), typeof c == "object" && c && typeof c.then == "function" ? ks(e, t, _a(c, r), fu(e)) : ks(e, t, r, fu(e));
		} catch (n) {
			ks(e, t, {
				then: function() {},
				status: "rejected",
				reason: n
			}, fu());
		} finally {
			j.p = a, o !== null && s.types !== null && (o.types = s.types), A.T = o;
		}
	}
	function ys() {}
	function bs(e, t, n, r) {
		if (e.tag !== 5) throw Error(i(476));
		var a = xs(e).queue;
		vs(e, a, t, oe, n === null ? ys : function() {
			return Ss(e), n(r);
		});
	}
	function xs(e) {
		var t = e.memoizedState;
		if (t !== null) return t;
		t = {
			memoizedState: oe,
			baseState: oe,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: jo,
				lastRenderedState: oe
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
				lastRenderedReducer: jo,
				lastRenderedState: n
			},
			next: null
		}, e.memoizedState = t, e = e.alternate, e !== null && (e.memoizedState = t), t;
	}
	function Ss(e) {
		var t = xs(e);
		t.next === null && (t = e.alternate.memoizedState), ks(e, t.next.queue, {}, fu());
	}
	function Cs() {
		return R(Qf);
	}
	function ws() {
		return Eo().memoizedState;
	}
	function Ts() {
		return Eo().memoizedState;
	}
	function Es(e) {
		for (var t = e.return; t !== null;) {
			switch (t.tag) {
				case 24:
				case 3:
					var n = fu();
					e = B(n);
					var r = Ua(t, e, n);
					r !== null && (mu(r, t, n), Wa(r, t, n)), t = { cache: la() }, e.payload = t;
					return;
			}
			t = t.return;
		}
	}
	function Ds(e, t, n) {
		var r = fu();
		n = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, js(e) ? Ms(t, n) : (n = ii(e, t, n, r), n !== null && (mu(n, e, r), Ns(n, t, r)));
	}
	function Os(e, t, n) {
		ks(e, t, n, fu());
	}
	function ks(e, t, n, r) {
		var i = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (js(e)) Ms(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, wr(s, o)) return ri(e, t, i, 0), Ll === null && ni(), !1;
			} catch {}
			if (n = ii(e, t, i, r), n !== null) return mu(n, e, r), Ns(n, t, r), !0;
		}
		return !1;
	}
	function As(e, t, n, r) {
		if (r = {
			lane: 2,
			revertLane: ud(),
			gesture: null,
			action: r,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, js(e)) {
			if (t) throw Error(i(479));
		} else t = ii(e, n, r, 2), t !== null && mu(t, e, 2);
	}
	function js(e) {
		var t = e.alternate;
		return e === K || t !== null && t === K;
	}
	function Ms(e, t) {
		lo = co = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function Ns(e, t, n) {
		if (n & 4194048) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, at(e, n);
		}
	}
	var Ps = {
		readContext: R,
		use: ko,
		useCallback: go,
		useContext: go,
		useEffect: go,
		useImperativeHandle: go,
		useLayoutEffect: go,
		useInsertionEffect: go,
		useMemo: go,
		useReducer: go,
		useRef: go,
		useState: go,
		useDebugValue: go,
		useDeferredValue: go,
		useTransition: go,
		useSyncExternalStore: go,
		useId: go,
		useHostTransitionStatus: go,
		useFormState: go,
		useActionState: go,
		useOptimistic: go,
		useMemoCache: go,
		useCacheRefresh: go
	};
	Ps.useEffectEvent = go;
	var Fs = {
		readContext: R,
		use: ko,
		useCallback: function(e, t) {
			return To().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: R,
		useEffect: as,
		useImperativeHandle: function(e, t, n) {
			n = n == null ? null : n.concat([e]), rs(4194308, 4, ds.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return rs(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			rs(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = To();
			t = t === void 0 ? null : t;
			var r = e();
			if (uo) {
				He(!0);
				try {
					e();
				} finally {
					He(!1);
				}
			}
			return n.memoizedState = [r, t], r;
		},
		useReducer: function(e, t, n) {
			var r = To();
			if (n !== void 0) {
				var i = n(t);
				if (uo) {
					He(!0);
					try {
						n(t);
					} finally {
						He(!1);
					}
				}
			} else i = t;
			return r.memoizedState = r.baseState = i, e = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: i
			}, r.queue = e, e = e.dispatch = Ds.bind(null, K, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = To();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: function(e) {
			e = Vo(e);
			var t = e.queue, n = Os.bind(null, K, t);
			return t.dispatch = n, [e.memoizedState, n];
		},
		useDebugValue: ps,
		useDeferredValue: function(e, t) {
			return gs(To(), e, t);
		},
		useTransition: function() {
			var e = Vo(!1);
			return e = vs.bind(null, K, e.queue, !0, !1), To().memoizedState = e, [!1, e];
		},
		useSyncExternalStore: function(e, t, n) {
			var r = K, a = To();
			if (L) {
				if (n === void 0) throw Error(i(407));
				n = n();
			} else {
				if (n = t(), Ll === null) throw Error(i(349));
				X & 127 || Io(r, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, as(Ro.bind(null, r, o, e), [e]), r.flags |= 2048, ts(9, { destroy: void 0 }, Lo.bind(null, r, o, n, t), null), n;
		},
		useId: function() {
			var e = To(), t = Ll.identifierPrefix;
			if (L) {
				var n = ki, r = Oi;
				n = (r & ~(1 << 32 - Ue(r) - 1)).toString(32) + n, t = "_" + t + "R_" + n, n = fo++, 0 < n && (t += "H" + n.toString(32)), t += "_";
			} else n = ho++, t = "_" + t + "r_" + n.toString(32) + "_";
			return e.memoizedState = t;
		},
		useHostTransitionStatus: Cs,
		useFormState: Xo,
		useActionState: Xo,
		useOptimistic: function(e) {
			var t = To();
			t.memoizedState = t.baseState = e;
			var n = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: null,
				lastRenderedState: null
			};
			return t.queue = n, t = As.bind(null, K, !0, n), n.dispatch = t, [e, t];
		},
		useMemoCache: Ao,
		useCacheRefresh: function() {
			return To().memoizedState = Es.bind(null, K);
		},
		useEffectEvent: function(e) {
			var t = To(), n = { impl: e };
			return t.memoizedState = n, function() {
				if (J & 2) throw Error(i(440));
				return n.impl.apply(void 0, arguments);
			};
		}
	}, Is = {
		readContext: R,
		use: ko,
		useCallback: ms,
		useContext: R,
		useEffect: os,
		useImperativeHandle: fs,
		useInsertionEffect: ls,
		useLayoutEffect: us,
		useMemo: hs,
		useReducer: Mo,
		useRef: ns,
		useState: function() {
			return Mo(jo);
		},
		useDebugValue: ps,
		useDeferredValue: function(e, t) {
			return _s(Eo(), q.memoizedState, e, t);
		},
		useTransition: function() {
			var e = Mo(jo)[0], t = Eo().memoizedState;
			return [typeof e == "boolean" ? e : Oo(e), t];
		},
		useSyncExternalStore: Fo,
		useId: ws,
		useHostTransitionStatus: Cs,
		useFormState: Zo,
		useActionState: Zo,
		useOptimistic: function(e, t) {
			return Ho(Eo(), q, e, t);
		},
		useMemoCache: Ao,
		useCacheRefresh: Ts
	};
	Is.useEffectEvent = cs;
	var Ls = {
		readContext: R,
		use: ko,
		useCallback: ms,
		useContext: R,
		useEffect: os,
		useImperativeHandle: fs,
		useInsertionEffect: ls,
		useLayoutEffect: us,
		useMemo: hs,
		useReducer: Po,
		useRef: ns,
		useState: function() {
			return Po(jo);
		},
		useDebugValue: ps,
		useDeferredValue: function(e, t) {
			var n = Eo();
			return q === null ? gs(n, e, t) : _s(n, q.memoizedState, e, t);
		},
		useTransition: function() {
			var e = Po(jo)[0], t = Eo().memoizedState;
			return [typeof e == "boolean" ? e : Oo(e), t];
		},
		useSyncExternalStore: Fo,
		useId: ws,
		useHostTransitionStatus: Cs,
		useFormState: es,
		useActionState: es,
		useOptimistic: function(e, t) {
			var n = Eo();
			return q === null ? (n.baseState = e, [e, n.queue.dispatch]) : Ho(n, q, e, t);
		},
		useMemoCache: Ao,
		useCacheRefresh: Ts
	};
	Ls.useEffectEvent = cs;
	function Rs(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : h({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var zs = {
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = fu(), i = B(r);
			i.payload = t, n != null && (i.callback = n), t = Ua(e, i, r), t !== null && (mu(t, e, r), Wa(t, e, r));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = fu(), i = B(r);
			i.tag = 1, i.payload = t, n != null && (i.callback = n), t = Ua(e, i, r), t !== null && (mu(t, e, r), Wa(t, e, r));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = fu(), r = B(n);
			r.tag = 2, t != null && (r.callback = t), t = Ua(e, r, n), t !== null && (mu(t, e, n), Wa(t, e, n));
		}
	};
	function Bs(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Tr(n, r) || !Tr(i, a) : !0;
	}
	function Vs(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && zs.enqueueReplaceState(t, t.state, null);
	}
	function Hs(e, t) {
		var n = t;
		if ("ref" in t) for (var r in n = {}, t) r !== "ref" && (n[r] = t[r]);
		if (e = e.defaultProps) for (var i in n === t && (n = h({}, n)), e) n[i] === void 0 && (n[i] = e[i]);
		return n;
	}
	function Us(e) {
		Qr(e);
	}
	function Ws(e) {
		console.error(e);
	}
	function Gs(e) {
		Qr(e);
	}
	function Ks(e, t) {
		try {
			var n = e.onUncaughtError;
			n(t.value, { componentStack: t.stack });
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function qs(e, t, n) {
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
	function Js(e, t, n) {
		return n = B(n), n.tag = 3, n.payload = { element: null }, n.callback = function() {
			Ks(e, t);
		}, n;
	}
	function Ys(e) {
		return e = B(e), e.tag = 3, e;
	}
	function Xs(e, t, n, r) {
		var i = n.type.getDerivedStateFromError;
		if (typeof i == "function") {
			var a = r.value;
			e.payload = function() {
				return i(a);
			}, e.callback = function() {
				qs(t, n, r);
			};
		}
		var o = n.stateNode;
		o !== null && typeof o.componentDidCatch == "function" && (e.callback = function() {
			qs(t, n, r), typeof i != "function" && (nu === null ? nu = /* @__PURE__ */ new Set([this]) : nu.add(this));
			var e = r.stack;
			this.componentDidCatch(r.value, { componentStack: e === null ? "" : e });
		});
	}
	function Zs(e, t, n, r, a) {
		if (n.flags |= 32768, typeof r == "object" && r && typeof r.then == "function") {
			if (t = n.alternate, t !== null && ea(t, n, a, !0), n = Za.current, n !== null) {
				switch (n.tag) {
					case 31:
					case 13: return Qa === null ? Eu() : n.alternate === null && Ul === 0 && (Ul = 3), n.flags &= -257, n.flags |= 65536, n.lanes = a, r === Ea ? n.flags |= 16384 : (t = n.updateQueue, t === null ? n.updateQueue = /* @__PURE__ */ new Set([r]) : t.add(r), Wu(e, r, a)), !1;
					case 22: return n.flags |= 65536, r === Ea ? n.flags |= 16384 : (t = n.updateQueue, t === null ? (t = {
						transitions: null,
						markerInstances: null,
						retryQueue: /* @__PURE__ */ new Set([r])
					}, n.updateQueue = t) : (n = t.retryQueue, n === null ? t.retryQueue = /* @__PURE__ */ new Set([r]) : n.add(r)), Wu(e, r, a)), !1;
				}
				throw Error(i(435, n.tag));
			}
			return Wu(e, r, a), Eu(), !1;
		}
		if (L) return t = Za.current, t === null ? (r !== zi && (t = Error(i(423), { cause: r }), Ki(bi(t, n))), e = e.current.alternate, e.flags |= 65536, a &= -a, e.lanes |= a, r = bi(r, n), a = Js(e.stateNode, r, a), Ga(e, a), Ul !== 4 && (Ul = 2)) : (!(t.flags & 65536) && (t.flags |= 256), t.flags |= 65536, t.lanes = a, r !== zi && (e = Error(i(422), { cause: r }), Ki(bi(e, n)))), !1;
		var o = Error(i(520), { cause: r });
		if (o = bi(o, n), Yl === null ? Yl = [o] : Yl.push(o), Ul !== 4 && (Ul = 2), t === null) return !0;
		r = bi(r, n), n = t;
		do {
			switch (n.tag) {
				case 3: return n.flags |= 65536, e = a & -a, n.lanes |= e, e = Js(n.stateNode, r, e), Ga(n, e), !1;
				case 1: if (t = n.type, o = n.stateNode, !(n.flags & 128) && (typeof t.getDerivedStateFromError == "function" || o !== null && typeof o.componentDidCatch == "function" && (nu === null || !nu.has(o)))) return n.flags |= 65536, a &= -a, n.lanes |= a, a = Ys(a), Xs(a, e, n, r), Ga(n, a), !1;
			}
			n = n.return;
		} while (n !== null);
		return !1;
	}
	var Qs = Error(i(461)), $s = !1;
	function ec(e, t, n, r) {
		t.child = e === null ? z(t, null, n, r) : za(t, e.child, n, r);
	}
	function tc(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		if ("ref" in r) {
			var o = {};
			for (var s in r) s !== "ref" && (o[s] = r[s]);
		} else o = r;
		return na(t), r = vo(e, t, n, o, a, i), s = So(), e !== null && !$s ? (Co(e, t, i), Tc(e, t, i)) : (L && s && Mi(t), t.flags |= 1, ec(e, t, r, i), t.child);
	}
	function nc(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !di(a) && a.defaultProps === void 0 && n.compare === null ? (t.tag = 15, t.type = a, rc(e, t, a, r, i)) : (e = mi(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, !Ec(e, i)) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Tr : n, n(o, r) && e.ref === t.ref) return Tc(e, t, i);
		}
		return t.flags |= 1, e = fi(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function rc(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Tr(a, r) && e.ref === t.ref) {
				if ($s = !1, t.pendingProps = r = a, Ec(e, i)) e.flags & 131072 && ($s = !0);
				else return t.lanes = e.lanes, Tc(e, t, i);
			}
		}
		return dc(e, t, n, r, i);
	}
	function ic(e, t, n, r) {
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
				return oc(e, t, a, n, r);
			}
			if (n & 536870912) t.memoizedState = {
				baseLanes: 0,
				cachePool: null
			}, e !== null && xa(t, a === null ? null : a.cachePool), a === null ? G() : W(t, a), to(t);
			else return r = t.lanes = 536870912, oc(e, t, a === null ? n : a.baseLanes | n, n, r);
		} else a === null ? (e !== null && xa(t, null), G(), no(t)) : (xa(t, a.cachePool), W(t, a), no(t), t.memoizedState = null);
		return ec(e, t, i, n), t.child;
	}
	function ac(e, t) {
		return e !== null && e.tag === 22 || t.stateNode !== null || (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), t.sibling;
	}
	function oc(e, t, n, r, i) {
		var a = ba();
		return a = a === null ? null : {
			parent: ca._currentValue,
			pool: a
		}, t.memoizedState = {
			baseLanes: n,
			cachePool: a
		}, e !== null && xa(t, null), G(), to(t), e !== null && ea(e, t, r, !0), t.childLanes = i, null;
	}
	function sc(e, t) {
		return t = bc({
			mode: t.mode,
			children: t.children
		}, e.mode), t.ref = e.ref, e.child = t, t.return = e, t;
	}
	function cc(e, t, n) {
		return za(t, e.child, null, n), e = sc(t, t.pendingProps), e.flags |= 2, ro(t), t.memoizedState = null, e;
	}
	function lc(e, t, n) {
		var r = t.pendingProps, a = !!(t.flags & 128);
		if (t.flags &= -129, e === null) {
			if (L) {
				if (r.mode === "hidden") return e = sc(t, r), t.lanes = 536870912, ac(null, e);
				if (eo(t), (e = Ii) ? (e = rf(e, Ri), e = e !== null && e.data === "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Di === null ? null : {
						id: Oi,
						overflow: ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = _i(e), n.return = t, t.child = n, Fi = t, Ii = null)) : e = null, e === null) throw Bi(t);
				return t.lanes = 536870912, null;
			}
			return sc(t, r);
		}
		var o = e.memoizedState;
		if (o !== null) {
			var s = o.dehydrated;
			if (eo(t), a) {
				if (t.flags & 256) t.flags &= -257, t = cc(e, t, n);
				else if (t.memoizedState !== null) t.child = e.child, t.flags |= 128, t = null;
				else throw Error(i(558));
			} else if ($s || ea(e, t, n, !1), a = (n & e.childLanes) !== 0, $s || a) {
				if (r = Ll, r !== null && (s = ot(r, n), s !== 0 && s !== o.retryLane)) throw o.retryLane = s, ai(e, s), mu(r, e, s), Qs;
				Eu(), t = cc(e, t, n);
			} else e = o.treeContext, Ii = cf(s.nextSibling), Fi = t, L = !0, Li = null, Ri = !1, e !== null && Pi(t, e), t = sc(t, r), t.flags |= 4096;
			return t;
		}
		return e = fi(e.child, {
			mode: r.mode,
			children: r.children
		}), e.ref = t.ref, t.child = e, e.return = t, e;
	}
	function uc(e, t) {
		var n = t.ref;
		if (n === null) e !== null && e.ref !== null && (t.flags |= 4194816);
		else {
			if (typeof n != "function" && typeof n != "object") throw Error(i(284));
			(e === null || e.ref !== n) && (t.flags |= 4194816);
		}
	}
	function dc(e, t, n, r, i) {
		return na(t), n = vo(e, t, n, r, void 0, i), r = So(), e !== null && !$s ? (Co(e, t, i), Tc(e, t, i)) : (L && r && Mi(t), t.flags |= 1, ec(e, t, n, i), t.child);
	}
	function fc(e, t, n, r, i, a) {
		return na(t), t.updateQueue = null, n = bo(t, r, n, i), yo(e), r = So(), e !== null && !$s ? (Co(e, t, a), Tc(e, t, a)) : (L && r && Mi(t), t.flags |= 1, ec(e, t, n, a), t.child);
	}
	function pc(e, t, n, r, i) {
		if (na(t), t.stateNode === null) {
			var a = ci, o = n.contextType;
			typeof o == "object" && o && (a = R(o)), a = new n(r, a), t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, a.updater = zs, t.stateNode = a, a._reactInternals = t, a = t.stateNode, a.props = r, a.state = t.memoizedState, a.refs = {}, Va(t), o = n.contextType, a.context = typeof o == "object" && o ? R(o) : ci, a.state = t.memoizedState, o = n.getDerivedStateFromProps, typeof o == "function" && (Rs(t, n, o, r), a.state = t.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof a.getSnapshotBeforeUpdate == "function" || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (o = a.state, typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount(), o !== a.state && zs.enqueueReplaceState(a, a.state, null), qa(t, r, a, i), V(), a.state = t.memoizedState), typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !0;
		} else if (e === null) {
			a = t.stateNode;
			var s = t.memoizedProps, c = Hs(n, s);
			a.props = c;
			var l = a.context, u = n.contextType;
			o = ci, typeof u == "object" && u && (o = R(u));
			var d = n.getDerivedStateFromProps;
			u = typeof d == "function" || typeof a.getSnapshotBeforeUpdate == "function", s = t.pendingProps !== s, u || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (s || l !== o) && Vs(t, a, r, o), Ba = !1;
			var f = t.memoizedState;
			a.state = f, qa(t, r, a, i), V(), l = t.memoizedState, s || f !== l || Ba ? (typeof d == "function" && (Rs(t, n, d, r), l = t.memoizedState), (c = Ba || Bs(t, n, c, r, f, l, o)) ? (u || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = l), a.props = r, a.state = l, a.context = o, r = c) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			a = t.stateNode, Ha(e, t), o = t.memoizedProps, u = Hs(n, o), a.props = u, d = t.pendingProps, f = a.context, l = n.contextType, c = ci, typeof l == "object" && l && (c = R(l)), s = n.getDerivedStateFromProps, (l = typeof s == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (o !== d || f !== c) && Vs(t, a, r, c), Ba = !1, f = t.memoizedState, a.state = f, qa(t, r, a, i), V();
			var p = t.memoizedState;
			o !== d || f !== p || Ba || e !== null && e.dependencies !== null && ta(e.dependencies) ? (typeof s == "function" && (Rs(t, n, s, r), p = t.memoizedState), (u = Ba || Bs(t, n, u, r, f, p, c) || e !== null && e.dependencies !== null && ta(e.dependencies)) ? (l || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(r, p, c), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(r, p, c)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = p), a.props = r, a.state = p, a.context = c, r = u) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return a = r, uc(e, t), r = !!(t.flags & 128), a || r ? (a = t.stateNode, n = r && typeof n.getDerivedStateFromError != "function" ? null : a.render(), t.flags |= 1, e !== null && r ? (t.child = za(t, e.child, null, i), t.child = za(t, null, n, i)) : ec(e, t, n, i), t.memoizedState = a.state, e = t.child) : e = Tc(e, t, i), e;
	}
	function mc(e, t, n, r) {
		return Wi(), t.flags |= 256, ec(e, t, n, r), t.child;
	}
	var hc = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0,
		hydrationErrors: null
	};
	function gc(e) {
		return {
			baseLanes: e,
			cachePool: Sa()
		};
	}
	function _c(e, t, n) {
		return e = e === null ? 0 : e.childLanes & ~n, t && (e |= ql), e;
	}
	function vc(e, t, n) {
		var r = t.pendingProps, a = !1, o = !!(t.flags & 128), s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : !!(io.current & 2)), s && (a = !0, t.flags &= -129), s = !!(t.flags & 32), t.flags &= -33, e === null) {
			if (L) {
				if (a ? $a(t) : no(t), (e = Ii) ? (e = rf(e, Ri), e = e !== null && e.data !== "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Di === null ? null : {
						id: Oi,
						overflow: ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = _i(e), n.return = t, t.child = n, Fi = t, Ii = null)) : e = null, e === null) throw Bi(t);
				return of(e) ? t.lanes = 32 : t.lanes = 536870912, null;
			}
			var c = r.children;
			return r = r.fallback, a ? (no(t), a = t.mode, c = bc({
				mode: "hidden",
				children: c
			}, a), r = hi(r, a, n, null), c.return = t, r.return = t, c.sibling = r, t.child = c, r = t.child, r.memoizedState = gc(n), r.childLanes = _c(e, s, n), t.memoizedState = hc, ac(null, r)) : ($a(t), yc(t, c));
		}
		var l = e.memoizedState;
		if (l !== null && (c = l.dehydrated, c !== null)) {
			if (o) t.flags & 256 ? ($a(t), t.flags &= -257, t = xc(e, t, n)) : t.memoizedState === null ? (no(t), c = r.fallback, a = t.mode, r = bc({
				mode: "visible",
				children: r.children
			}, a), c = hi(c, a, n, null), c.flags |= 2, r.return = t, c.return = t, r.sibling = c, t.child = r, za(t, e.child, null, n), r = t.child, r.memoizedState = gc(n), r.childLanes = _c(e, s, n), t.memoizedState = hc, t = ac(null, r)) : (no(t), t.child = e.child, t.flags |= 128, t = null);
			else if ($a(t), of(c)) {
				if (s = c.nextSibling && c.nextSibling.dataset, s) var u = s.dgst;
				s = u, r = Error(i(419)), r.stack = "", r.digest = s, Ki({
					value: r,
					source: null,
					stack: null
				}), t = xc(e, t, n);
			} else if ($s || ea(e, t, n, !1), s = (n & e.childLanes) !== 0, $s || s) {
				if (s = Ll, s !== null && (r = ot(s, n), r !== 0 && r !== l.retryLane)) throw l.retryLane = r, ai(e, r), mu(s, e, r), Qs;
				af(c) || Eu(), t = xc(e, t, n);
			} else af(c) ? (t.flags |= 192, t.child = e.child, t = null) : (e = l.treeContext, Ii = cf(c.nextSibling), Fi = t, L = !0, Li = null, Ri = !1, e !== null && Pi(t, e), t = yc(t, r.children), t.flags |= 4096);
			return t;
		}
		return a ? (no(t), c = r.fallback, a = t.mode, l = e.child, u = l.sibling, r = fi(l, {
			mode: "hidden",
			children: r.children
		}), r.subtreeFlags = l.subtreeFlags & 65011712, u === null ? (c = hi(c, a, n, null), c.flags |= 2) : c = fi(u, c), c.return = t, r.return = t, r.sibling = c, t.child = r, ac(null, r), r = t.child, c = e.child.memoizedState, c === null ? c = gc(n) : (a = c.cachePool, a === null ? a = Sa() : (l = ca._currentValue, a = a.parent === l ? a : {
			parent: l,
			pool: l
		}), c = {
			baseLanes: c.baseLanes | n,
			cachePool: a
		}), r.memoizedState = c, r.childLanes = _c(e, s, n), t.memoizedState = hc, ac(e.child, r)) : ($a(t), n = e.child, e = n.sibling, n = fi(n, {
			mode: "visible",
			children: r.children
		}), n.return = t, n.sibling = null, e !== null && (s = t.deletions, s === null ? (t.deletions = [e], t.flags |= 16) : s.push(e)), t.child = n, t.memoizedState = null, n);
	}
	function yc(e, t) {
		return t = bc({
			mode: "visible",
			children: t
		}, e.mode), t.return = e, e.child = t;
	}
	function bc(e, t) {
		return e = ui(22, e, null, t), e.lanes = 0, e;
	}
	function xc(e, t, n) {
		return za(t, e.child, null, n), e = yc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function Sc(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), Qi(e.return, t, n);
	}
	function Cc(e, t, n, r, i, a) {
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
	function wc(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		r = r.children;
		var o = io.current, s = !!(o & 2);
		if (s ? (o = o & 1 | 2, t.flags |= 128) : o &= 1, M(io, o), ec(e, t, r, n), r = L ? wi : 0, !s && e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
			if (e.tag === 13) e.memoizedState !== null && Sc(e, n, t);
			else if (e.tag === 19) Sc(e, n, t);
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
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && ao(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), Cc(t, !1, i, n, a, r);
				break;
			case "backwards":
			case "unstable_legacy-backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && ao(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				Cc(t, !0, n, null, a, r);
				break;
			case "together":
				Cc(t, !1, null, null, void 0, r);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function Tc(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), Wl |= t.lanes, (n & t.childLanes) === 0) {
			if (e !== null) {
				if (ea(e, t, n, !1), (n & t.childLanes) === 0) return null;
			} else return null;
		}
		if (e !== null && t.child !== e.child) throw Error(i(153));
		if (t.child !== null) {
			for (e = t.child, n = fi(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = fi(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function Ec(e, t) {
		return (e.lanes & t) !== 0 || (e = e.dependencies, !!(e !== null && ta(e)));
	}
	function Dc(e, t, n) {
		switch (t.tag) {
			case 3:
				he(t, t.stateNode.containerInfo), Xi(t, ca, e.memoizedState.cache), Wi();
				break;
			case 27:
			case 5:
				_e(t);
				break;
			case 4:
				he(t, t.stateNode.containerInfo);
				break;
			case 10:
				Xi(t, t.type, t.memoizedProps.value);
				break;
			case 31:
				if (t.memoizedState !== null) return t.flags |= 128, eo(t), null;
				break;
			case 13:
				var r = t.memoizedState;
				if (r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? ($a(t), e = Tc(e, t, n), e === null ? null : e.sibling) : vc(e, t, n) : ($a(t), t.flags |= 128, null);
				$a(t);
				break;
			case 19:
				var i = !!(e.flags & 128);
				if (r = (n & t.childLanes) !== 0, r || (ea(e, t, n, !1), r = (n & t.childLanes) !== 0), i) {
					if (r) return wc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), M(io, io.current), r) break;
				return null;
			case 22: return t.lanes = 0, ic(e, t, n, t.pendingProps);
			case 24: Xi(t, ca, e.memoizedState.cache);
		}
		return Tc(e, t, n);
	}
	function Oc(e, t, n) {
		if (e !== null) {
			if (e.memoizedProps !== t.pendingProps) $s = !0;
			else {
				if (!Ec(e, n) && !(t.flags & 128)) return $s = !1, Dc(e, t, n);
				$s = !!(e.flags & 131072);
			}
		} else $s = !1, L && t.flags & 1048576 && ji(t, wi, t.index);
		switch (t.lanes = 0, t.tag) {
			case 16:
				a: {
					var r = t.pendingProps;
					if (e = ka(t.elementType), t.type = e, typeof e == "function") di(e) ? (r = Hs(e, r), t.tag = 1, t = pc(null, t, e, r, n)) : (t.tag = 0, t = dc(null, t, e, r, n));
					else {
						if (e != null) {
							var a = e.$$typeof;
							if (a === w) {
								t.tag = 11, t = tc(null, t, e, r, n);
								break a;
							}
							if (a === E) {
								t.tag = 14, t = nc(null, t, e, r, n);
								break a;
							}
						}
						throw t = ie(e) || e, Error(i(306, t, ""));
					}
				}
				return t;
			case 0: return dc(e, t, t.type, t.pendingProps, n);
			case 1: return r = t.type, a = Hs(r, t.pendingProps), pc(e, t, r, a, n);
			case 3:
				a: {
					if (he(t, t.stateNode.containerInfo), e === null) throw Error(i(387));
					r = t.pendingProps;
					var o = t.memoizedState;
					a = o.element, Ha(e, t), qa(t, r, null, n);
					var s = t.memoizedState;
					if (r = s.cache, Xi(t, ca, r), r !== o.cache && $i(t, [ca], n, !0), V(), r = s.element, o.isDehydrated) {
						if (o = {
							element: r,
							isDehydrated: !1,
							cache: s.cache
						}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
							t = mc(e, t, r, n);
							break a;
						}
						if (r !== a) {
							a = bi(Error(i(424)), t), Ki(a), t = mc(e, t, r, n);
							break a;
						}
						switch (e = t.stateNode.containerInfo, e.nodeType) {
							case 9:
								e = e.body;
								break;
							default: e = e.nodeName === "HTML" ? e.ownerDocument.body : e;
						}
						for (Ii = cf(e.firstChild), Fi = t, L = !0, Li = null, Ri = !0, n = z(t, null, r, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					} else {
						if (Wi(), r === a) {
							t = Tc(e, t, n);
							break a;
						}
						ec(e, t, r, n);
					}
					t = t.child;
				}
				return t;
			case 26: return uc(e, t), e === null ? (n = kf(t.type, null, t.pendingProps, null)) ? t.memoizedState = n : L || (n = t.type, e = t.pendingProps, r = Bd(pe.current).createElement(n), r[ft] = t, r[pt] = e, Pd(r, n, e), Tt(r), t.stateNode = r) : t.memoizedState = kf(t.type, e.memoizedProps, t.pendingProps, e.memoizedState), null;
			case 27: return _e(t), e === null && L && (r = t.stateNode = ff(t.type, t.pendingProps, pe.current), Fi = t, Ri = !0, a = Ii, Zd(t.type) ? (lf = a, Ii = cf(r.firstChild)) : Ii = a), ec(e, t, t.pendingProps.children, n), uc(e, t), e === null && (t.flags |= 4194304), t.child;
			case 5: return e === null && L && ((a = r = Ii) && (r = tf(r, t.type, t.pendingProps, Ri), r === null ? a = !1 : (t.stateNode = r, Fi = t, Ii = cf(r.firstChild), Ri = !1, a = !0)), a || Bi(t)), _e(t), a = t.type, o = t.pendingProps, s = e === null ? null : e.memoizedProps, r = o.children, Ud(a, o) ? r = null : s !== null && Ud(a, s) && (t.flags |= 32), t.memoizedState !== null && (a = vo(e, t, xo, null, null, n), Qf._currentValue = a), uc(e, t), ec(e, t, r, n), t.child;
			case 6: return e === null && L && ((e = n = Ii) && (n = nf(n, t.pendingProps, Ri), n === null ? e = !1 : (t.stateNode = n, Fi = t, Ii = null, e = !0)), e || Bi(t)), null;
			case 13: return vc(e, t, n);
			case 4: return he(t, t.stateNode.containerInfo), r = t.pendingProps, e === null ? t.child = za(t, null, r, n) : ec(e, t, r, n), t.child;
			case 11: return tc(e, t, t.type, t.pendingProps, n);
			case 7: return ec(e, t, t.pendingProps, n), t.child;
			case 8: return ec(e, t, t.pendingProps.children, n), t.child;
			case 12: return ec(e, t, t.pendingProps.children, n), t.child;
			case 10: return r = t.pendingProps, Xi(t, t.type, r.value), ec(e, t, r.children, n), t.child;
			case 9: return a = t.type._context, r = t.pendingProps.children, na(t), a = R(a), r = r(a), t.flags |= 1, ec(e, t, r, n), t.child;
			case 14: return nc(e, t, t.type, t.pendingProps, n);
			case 15: return rc(e, t, t.type, t.pendingProps, n);
			case 19: return wc(e, t, n);
			case 31: return lc(e, t, n);
			case 22: return ic(e, t, n, t.pendingProps);
			case 24: return na(t), r = R(ca), e === null ? (a = ba(), a === null && (a = Ll, o = la(), a.pooledCache = o, o.refCount++, o !== null && (a.pooledCacheLanes |= n), a = o), t.memoizedState = {
				parent: r,
				cache: a
			}, Va(t), Xi(t, ca, a)) : ((e.lanes & n) !== 0 && (Ha(e, t), qa(t, null, null, n), V()), a = e.memoizedState, o = t.memoizedState, a.parent === r ? (r = o.cache, Xi(t, ca, r), r !== a.cache && $i(t, [ca], n, !0)) : (a = {
				parent: r,
				cache: r
			}, t.memoizedState = a, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = a), Xi(t, ca, r))), ec(e, t, t.pendingProps.children, n), t.child;
			case 29: throw t.pendingProps;
		}
		throw Error(i(156, t.tag));
	}
	function kc(e) {
		e.flags |= 4;
	}
	function Ac(e, t, n, r, i) {
		if ((t = !!(e.mode & 32)) && (t = !1), t) {
			if (e.flags |= 16777216, (i & 335544128) === i) {
				if (e.stateNode.complete) e.flags |= 8192;
				else if (Cu()) e.flags |= 8192;
				else throw Aa = Ea, wa;
			}
		} else e.flags &= -16777217;
	}
	function jc(e, t) {
		if (t.type !== "stylesheet" || t.state.loading & 4) e.flags &= -16777217;
		else if (e.flags |= 16777216, !Wf(t)) {
			if (Cu()) e.flags |= 8192;
			else throw Aa = Ea, wa;
		}
	}
	function Mc(e, t) {
		t !== null && (e.flags |= 4), e.flags & 16384 && (t = e.tag === 22 ? 536870912 : et(), e.lanes |= t, Jl |= t);
	}
	function Nc(e, t) {
		if (!L) switch (e.tailMode) {
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
	function Pc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 65011712, r |= i.flags & 65011712, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function Fc(e, t, n) {
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
			case 14: return Pc(t), null;
			case 1: return Pc(t), null;
			case 3: return n = t.stateNode, r = null, e !== null && (r = e.memoizedState.cache), t.memoizedState.cache !== r && (t.flags |= 2048), Zi(ca), ge(), n.pendingContext && (n.context = n.pendingContext, n.pendingContext = null), (e === null || e.child === null) && (Ui(t) ? kc(t) : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Gi())), Pc(t), null;
			case 26:
				var a = t.type, o = t.memoizedState;
				return e === null ? (kc(t), o === null ? (Pc(t), Ac(t, a, null, r, n)) : (Pc(t), jc(t, o))) : o ? o === e.memoizedState ? (Pc(t), t.flags &= -16777217) : (kc(t), Pc(t), jc(t, o)) : (e = e.memoizedProps, e !== r && kc(t), Pc(t), Ac(t, a, e, r, n)), null;
			case 27:
				if (ve(t), n = pe.current, a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && kc(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return Pc(t), null;
					}
					e = de.current, Ui(t) ? Vi(t, e) : (e = ff(a, r, n), t.stateNode = e, kc(t));
				}
				return Pc(t), null;
			case 5:
				if (ve(t), a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && kc(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return Pc(t), null;
					}
					if (o = de.current, Ui(t)) Vi(t, o);
					else {
						var s = Bd(pe.current);
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
						o[ft] = t, o[pt] = r;
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
						r && kc(t);
					}
				}
				return Pc(t), Ac(t, t.type, e === null ? null : e.memoizedProps, t.pendingProps, n), null;
			case 6:
				if (e && t.stateNode != null) e.memoizedProps !== r && kc(t);
				else {
					if (typeof r != "string" && t.stateNode === null) throw Error(i(166));
					if (e = pe.current, Ui(t)) {
						if (e = t.stateNode, n = t.memoizedProps, r = null, a = Fi, a !== null) switch (a.tag) {
							case 27:
							case 5: r = a.memoizedProps;
						}
						e[ft] = t, e = !!(e.nodeValue === n || r !== null && !0 === r.suppressHydrationWarning || jd(e.nodeValue, n)), e || Bi(t, !0);
					} else e = Bd(e).createTextNode(r), e[ft] = t, t.stateNode = e;
				}
				return Pc(t), null;
			case 31:
				if (n = t.memoizedState, e === null || e.memoizedState !== null) {
					if (r = Ui(t), n !== null) {
						if (e === null) {
							if (!r) throw Error(i(318));
							if (e = t.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(557));
							e[ft] = t;
						} else Wi(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						Pc(t), e = !1;
					} else n = Gi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = n), e = !0;
					if (!e) return t.flags & 256 ? (ro(t), t) : (ro(t), null);
					if (t.flags & 128) throw Error(i(558));
				}
				return Pc(t), null;
			case 13:
				if (r = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (a = Ui(t), r !== null && r.dehydrated !== null) {
						if (e === null) {
							if (!a) throw Error(i(318));
							if (a = t.memoizedState, a = a === null ? null : a.dehydrated, !a) throw Error(i(317));
							a[ft] = t;
						} else Wi(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						Pc(t), a = !1;
					} else a = Gi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = a), a = !0;
					if (!a) return t.flags & 256 ? (ro(t), t) : (ro(t), null);
				}
				return ro(t), t.flags & 128 ? (t.lanes = n, t) : (n = r !== null, e = e !== null && e.memoizedState !== null, n && (r = t.child, a = null, r.alternate !== null && r.alternate.memoizedState !== null && r.alternate.memoizedState.cachePool !== null && (a = r.alternate.memoizedState.cachePool.pool), o = null, r.memoizedState !== null && r.memoizedState.cachePool !== null && (o = r.memoizedState.cachePool.pool), o !== a && (r.flags |= 2048)), n !== e && n && (t.child.flags |= 8192), Mc(t, t.updateQueue), Pc(t), null);
			case 4: return ge(), e === null && xd(t.stateNode.containerInfo), Pc(t), null;
			case 10: return Zi(t.type), Pc(t), null;
			case 19:
				if (ue(io), r = t.memoizedState, r === null) return Pc(t), null;
				if (a = !!(t.flags & 128), o = r.rendering, o === null) {
					if (a) Nc(r, !1);
					else {
						if (Ul !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
							if (o = ao(e), o !== null) {
								for (t.flags |= 128, Nc(r, !1), e = o.updateQueue, t.updateQueue = e, Mc(t, e), t.subtreeFlags = 0, e = n, n = t.child; n !== null;) pi(n, e), n = n.sibling;
								return M(io, io.current & 1 | 2), L && Ai(t, r.treeForkCount), t.child;
							}
							e = e.sibling;
						}
						r.tail !== null && je() > eu && (t.flags |= 128, a = !0, Nc(r, !1), t.lanes = 4194304);
					}
				} else {
					if (!a) {
						if (e = ao(o), e !== null) {
							if (t.flags |= 128, a = !0, e = e.updateQueue, t.updateQueue = e, Mc(t, e), Nc(r, !0), r.tail === null && r.tailMode === "hidden" && !o.alternate && !L) return Pc(t), null;
						} else 2 * je() - r.renderingStartTime > eu && n !== 536870912 && (t.flags |= 128, a = !0, Nc(r, !1), t.lanes = 4194304);
					}
					r.isBackwards ? (o.sibling = t.child, t.child = o) : (e = r.last, e === null ? t.child = o : e.sibling = o, r.last = o);
				}
				return r.tail === null ? (Pc(t), null) : (e = r.tail, r.rendering = e, r.tail = e.sibling, r.renderingStartTime = je(), e.sibling = null, n = io.current, M(io, a ? n & 1 | 2 : n & 1), L && Ai(t, r.treeForkCount), e);
			case 22:
			case 23: return ro(t), Xa(), r = t.memoizedState !== null, e === null ? r && (t.flags |= 8192) : e.memoizedState !== null !== r && (t.flags |= 8192), r ? n & 536870912 && !(t.flags & 128) && (Pc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : Pc(t), n = t.updateQueue, n !== null && Mc(t, n.retryQueue), n = null, e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), r = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (r = t.memoizedState.cachePool.pool), r !== n && (t.flags |= 2048), e !== null && ue(ya), null;
			case 24: return n = null, e !== null && (n = e.memoizedState.cache), t.memoizedState.cache !== n && (t.flags |= 2048), Zi(ca), Pc(t), null;
			case 25: return null;
			case 30: return null;
		}
		throw Error(i(156, t.tag));
	}
	function Ic(e, t) {
		switch (Ni(t), t.tag) {
			case 1: return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return Zi(ca), ge(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 26:
			case 27:
			case 5: return ve(t), null;
			case 31:
				if (t.memoizedState !== null) {
					if (ro(t), t.alternate === null) throw Error(i(340));
					Wi();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 13:
				if (ro(t), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(i(340));
					Wi();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return ue(io), null;
			case 4: return ge(), null;
			case 10: return Zi(t.type), null;
			case 22:
			case 23: return ro(t), Xa(), e !== null && ue(ya), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 24: return Zi(ca), null;
			case 25: return null;
			default: return null;
		}
	}
	function Lc(e, t) {
		switch (Ni(t), t.tag) {
			case 3:
				Zi(ca), ge();
				break;
			case 26:
			case 27:
			case 5:
				ve(t);
				break;
			case 4:
				ge();
				break;
			case 31:
				t.memoizedState !== null && ro(t);
				break;
			case 13:
				ro(t);
				break;
			case 19:
				ue(io);
				break;
			case 10:
				Zi(t.type);
				break;
			case 22:
			case 23:
				ro(t), Xa(), e !== null && ue(ya);
				break;
			case 24: Zi(ca);
		}
	}
	function Rc(e, t) {
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
			Q(t, t.return, e);
		}
	}
	function zc(e, t, n) {
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
								Q(i, c, e);
							}
						}
					}
					r = r.next;
				} while (r !== a);
			}
		} catch (e) {
			Q(t, t.return, e);
		}
	}
	function Bc(e) {
		var t = e.updateQueue;
		if (t !== null) {
			var n = e.stateNode;
			try {
				H(t, n);
			} catch (t) {
				Q(e, e.return, t);
			}
		}
	}
	function Vc(e, t, n) {
		n.props = Hs(e.type, e.memoizedProps), n.state = e.memoizedState;
		try {
			n.componentWillUnmount();
		} catch (n) {
			Q(e, t, n);
		}
	}
	function Hc(e, t) {
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
			Q(e, t, n);
		}
	}
	function Uc(e, t) {
		var n = e.ref, r = e.refCleanup;
		if (n !== null) {
			if (typeof r == "function") try {
				r();
			} catch (n) {
				Q(e, t, n);
			} finally {
				e.refCleanup = null, e = e.alternate, e != null && (e.refCleanup = null);
			}
			else if (typeof n == "function") try {
				n(null);
			} catch (n) {
				Q(e, t, n);
			}
			else n.current = null;
		}
	}
	function Wc(e) {
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
			Q(e, e.return, t);
		}
	}
	function Gc(e, t, n) {
		try {
			var r = e.stateNode;
			Fd(r, e.type, n, t), r[pt] = t;
		} catch (t) {
			Q(e, e.return, t);
		}
	}
	function Kc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 26 || e.tag === 27 && Zd(e.type) || e.tag === 4;
	}
	function qc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || Kc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.tag === 27 && Zd(e.type) || e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Jc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? (n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n).insertBefore(e, t) : (t = n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n, t.appendChild(e), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = an));
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode, t = null), e = e.child, e !== null)) for (Jc(e, t, n), e = e.sibling; e !== null;) Jc(e, t, n), e = e.sibling;
	}
	function Yc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode), e = e.child, e !== null)) for (Yc(e, t, n), e = e.sibling; e !== null;) Yc(e, t, n), e = e.sibling;
	}
	function Xc(e) {
		var t = e.stateNode, n = e.memoizedProps;
		try {
			for (var r = e.type, i = t.attributes; i.length;) t.removeAttributeNode(i[0]);
			Pd(t, r, n), t[ft] = e, t[pt] = n;
		} catch (t) {
			Q(e, e.return, t);
		}
	}
	var Zc = !1, Qc = !1, $c = !1, el = typeof WeakSet == "function" ? WeakSet : Set, tl = null;
	function nl(e, t) {
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
		}, sp = !1, tl = t; tl !== null;) if (t = tl, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, tl = e;
		else for (; tl !== null;) {
			switch (t = tl, o = t.alternate, e = t.flags, t.tag) {
				case 0:
					if (e & 4 && (e = t.updateQueue, e = e === null ? null : e.events, e !== null)) for (n = 0; n < e.length; n++) a = e[n], a.ref.impl = a.nextImpl;
					break;
				case 11:
				case 15: break;
				case 1:
					if (e & 1024 && o !== null) {
						e = void 0, n = t, a = o.memoizedProps, o = o.memoizedState, r = n.stateNode;
						try {
							var h = Hs(n.type, a);
							e = r.getSnapshotBeforeUpdate(h, o), r.__reactInternalSnapshotBeforeUpdate = e;
						} catch (e) {
							Q(n, n.return, e);
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
				e.return = t.return, tl = e;
				break;
			}
			tl = t.return;
		}
	}
	function rl(e, t, n) {
		var r = n.flags;
		switch (n.tag) {
			case 0:
			case 11:
			case 15:
				vl(e, n), r & 4 && Rc(5, n);
				break;
			case 1:
				if (vl(e, n), r & 4) {
					if (e = n.stateNode, t === null) try {
						e.componentDidMount();
					} catch (e) {
						Q(n, n.return, e);
					}
					else {
						var i = Hs(n.type, t.memoizedProps);
						t = t.memoizedState;
						try {
							e.componentDidUpdate(i, t, e.__reactInternalSnapshotBeforeUpdate);
						} catch (e) {
							Q(n, n.return, e);
						}
					}
				}
				r & 64 && Bc(n), r & 512 && Hc(n, n.return);
				break;
			case 3:
				if (vl(e, n), r & 64 && (e = n.updateQueue, e !== null)) {
					if (t = null, n.child !== null) switch (n.child.tag) {
						case 27:
						case 5:
							t = n.child.stateNode;
							break;
						case 1: t = n.child.stateNode;
					}
					try {
						H(e, t);
					} catch (e) {
						Q(n, n.return, e);
					}
				}
				break;
			case 27: t === null && r & 4 && Xc(n);
			case 26:
			case 5:
				vl(e, n), t === null && r & 4 && Wc(n), r & 512 && Hc(n, n.return);
				break;
			case 12:
				vl(e, n);
				break;
			case 31:
				vl(e, n), r & 4 && ll(e, n);
				break;
			case 13:
				vl(e, n), r & 4 && ul(e, n), r & 64 && (e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null && (n = qu.bind(null, n), sf(e, n))));
				break;
			case 22:
				if (r = n.memoizedState !== null || Zc, !r) {
					t = t !== null && t.memoizedState !== null || Qc, i = Zc;
					var a = Qc;
					Zc = r, (Qc = t) && !a ? bl(e, n, !!(n.subtreeFlags & 8772)) : vl(e, n), Zc = i, Qc = a;
				}
				break;
			case 30: break;
			default: vl(e, n);
		}
	}
	function il(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, il(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && bt(t)), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	var al = null, ol = !1;
	function sl(e, t, n) {
		for (n = n.child; n !== null;) cl(e, t, n), n = n.sibling;
	}
	function cl(e, t, n) {
		if (Ve && typeof Ve.onCommitFiberUnmount == "function") try {
			Ve.onCommitFiberUnmount(Be, n);
		} catch {}
		switch (n.tag) {
			case 26:
				Qc || Uc(n, t), sl(e, t, n), n.memoizedState ? n.memoizedState.count-- : n.stateNode && (n = n.stateNode, n.parentNode.removeChild(n));
				break;
			case 27:
				Qc || Uc(n, t);
				var r = al, i = ol;
				Zd(n.type) && (al = n.stateNode, ol = !1), sl(e, t, n), pf(n.stateNode), al = r, ol = i;
				break;
			case 5: Qc || Uc(n, t);
			case 6:
				if (r = al, i = ol, al = null, sl(e, t, n), al = r, ol = i, al !== null) {
					if (ol) try {
						(al.nodeType === 9 ? al.body : al.nodeName === "HTML" ? al.ownerDocument.body : al).removeChild(n.stateNode);
					} catch (e) {
						Q(n, t, e);
					}
					else try {
						al.removeChild(n.stateNode);
					} catch (e) {
						Q(n, t, e);
					}
				}
				break;
			case 18:
				al !== null && (ol ? (e = al, Qd(e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, n.stateNode), Np(e)) : Qd(al, n.stateNode));
				break;
			case 4:
				r = al, i = ol, al = n.stateNode.containerInfo, ol = !0, sl(e, t, n), al = r, ol = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				zc(2, n, t), Qc || zc(4, n, t), sl(e, t, n);
				break;
			case 1:
				Qc || (Uc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function" && Vc(n, t, r)), sl(e, t, n);
				break;
			case 21:
				sl(e, t, n);
				break;
			case 22:
				Qc = (r = Qc) || n.memoizedState !== null, sl(e, t, n), Qc = r;
				break;
			default: sl(e, t, n);
		}
	}
	function ll(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null))) {
			e = e.dehydrated;
			try {
				Np(e);
			} catch (e) {
				Q(t, t.return, e);
			}
		}
	}
	function ul(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null && (e = e.dehydrated, e !== null)))) try {
			Np(e);
		} catch (e) {
			Q(t, t.return, e);
		}
	}
	function dl(e) {
		switch (e.tag) {
			case 31:
			case 13:
			case 19:
				var t = e.stateNode;
				return t === null && (t = e.stateNode = new el()), t;
			case 22: return e = e.stateNode, t = e._retryCache, t === null && (t = e._retryCache = new el()), t;
			default: throw Error(i(435, e.tag));
		}
	}
	function fl(e, t) {
		var n = dl(e);
		t.forEach(function(t) {
			if (!n.has(t)) {
				n.add(t);
				var r = Ju.bind(null, e, t);
				t.then(r, r);
			}
		});
	}
	function pl(e, t) {
		var n = t.deletions;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var a = n[r], o = e, s = t, c = s;
			a: for (; c !== null;) {
				switch (c.tag) {
					case 27:
						if (Zd(c.type)) {
							al = c.stateNode, ol = !1;
							break a;
						}
						break;
					case 5:
						al = c.stateNode, ol = !1;
						break a;
					case 3:
					case 4:
						al = c.stateNode.containerInfo, ol = !0;
						break a;
				}
				c = c.return;
			}
			if (al === null) throw Error(i(160));
			cl(o, s, a), al = null, ol = !1, o = a.alternate, o !== null && (o.return = null), a.return = null;
		}
		if (t.subtreeFlags & 13886) for (t = t.child; t !== null;) hl(t, e), t = t.sibling;
	}
	var ml = null;
	function hl(e, t) {
		var n = e.alternate, r = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				pl(t, e), gl(e), r & 4 && (zc(3, e, e.return), Rc(3, e), zc(5, e, e.return));
				break;
			case 1:
				pl(t, e), gl(e), r & 512 && (Qc || n === null || Uc(n, n.return)), r & 64 && Zc && (e = e.updateQueue, e !== null && (r = e.callbacks, r !== null && (n = e.shared.hiddenCallbacks, e.shared.hiddenCallbacks = n === null ? r : n.concat(r))));
				break;
			case 26:
				var a = ml;
				if (pl(t, e), gl(e), r & 512 && (Qc || n === null || Uc(n, n.return)), r & 4) {
					var o = n === null ? null : n.memoizedState;
					if (r = e.memoizedState, n === null) {
						if (r === null) {
							if (e.stateNode === null) {
								a: {
									r = e.type, n = e.memoizedProps, a = a.ownerDocument || a;
									b: switch (r) {
										case "title":
											o = a.getElementsByTagName("title")[0], (!o || o[yt] || o[ft] || o.namespaceURI === "http://www.w3.org/2000/svg" || o.hasAttribute("itemprop")) && (o = a.createElement(r), a.head.insertBefore(o, a.querySelector("head > title"))), Pd(o, r, n), o[ft] = e, Tt(o), r = o;
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
									o[ft] = e, Tt(o), r = o;
								}
								e.stateNode = r;
							} else Hf(a, e.type, e.stateNode);
						} else e.stateNode = If(a, r, e.memoizedProps);
					} else o === r ? r === null && e.stateNode !== null && Gc(e, e.memoizedProps, n.memoizedProps) : (o === null ? n.stateNode !== null && (n = n.stateNode, n.parentNode.removeChild(n)) : o.count--, r === null ? Hf(a, e.type, e.stateNode) : If(a, r, e.memoizedProps));
				}
				break;
			case 27:
				pl(t, e), gl(e), r & 512 && (Qc || n === null || Uc(n, n.return)), n !== null && r & 4 && Gc(e, e.memoizedProps, n.memoizedProps);
				break;
			case 5:
				if (pl(t, e), gl(e), r & 512 && (Qc || n === null || Uc(n, n.return)), e.flags & 32) {
					a = e.stateNode;
					try {
						Xt(a, "");
					} catch (t) {
						Q(e, e.return, t);
					}
				}
				r & 4 && e.stateNode != null && (a = e.memoizedProps, Gc(e, a, n === null ? a : n.memoizedProps)), r & 1024 && ($c = !0);
				break;
			case 6:
				if (pl(t, e), gl(e), r & 4) {
					if (e.stateNode === null) throw Error(i(162));
					r = e.memoizedProps, n = e.stateNode;
					try {
						n.nodeValue = r;
					} catch (t) {
						Q(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Bf = null, a = ml, ml = gf(t.containerInfo), pl(t, e), ml = a, gl(e), r & 4 && n !== null && n.memoizedState.isDehydrated) try {
					Np(t.containerInfo);
				} catch (t) {
					Q(e, e.return, t);
				}
				$c && ($c = !1, _l(e));
				break;
			case 4:
				r = ml, ml = gf(e.stateNode.containerInfo), pl(t, e), gl(e), ml = r;
				break;
			case 12:
				pl(t, e), gl(e);
				break;
			case 31:
				pl(t, e), gl(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, fl(e, r)));
				break;
			case 13:
				pl(t, e), gl(e), e.child.flags & 8192 && e.memoizedState !== null != (n !== null && n.memoizedState !== null) && (Ql = je()), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, fl(e, r)));
				break;
			case 22:
				a = e.memoizedState !== null;
				var l = n !== null && n.memoizedState !== null, u = Zc, d = Qc;
				if (Zc = u || a, Qc = d || l, pl(t, e), Qc = d, Zc = u, gl(e), r & 8192) a: for (t = e.stateNode, t._visibility = a ? t._visibility & -2 : t._visibility | 1, a && (n === null || l || Zc || Qc || yl(e)), n = null, t = e;;) {
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
								Q(l, l.return, e);
							}
						}
					} else if (t.tag === 6) {
						if (n === null) {
							l = t;
							try {
								l.stateNode.nodeValue = a ? "" : l.memoizedProps;
							} catch (e) {
								Q(l, l.return, e);
							}
						}
					} else if (t.tag === 18) {
						if (n === null) {
							l = t;
							try {
								var m = l.stateNode;
								a ? $d(m, !0) : $d(l.stateNode, !1);
							} catch (e) {
								Q(l, l.return, e);
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
				r & 4 && (r = e.updateQueue, r !== null && (n = r.retryQueue, n !== null && (r.retryQueue = null, fl(e, n))));
				break;
			case 19:
				pl(t, e), gl(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, fl(e, r)));
				break;
			case 30: break;
			case 21: break;
			default: pl(t, e), gl(e);
		}
	}
	function gl(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				for (var n, r = e.return; r !== null;) {
					if (Kc(r)) {
						n = r;
						break;
					}
					r = r.return;
				}
				if (n == null) throw Error(i(160));
				switch (n.tag) {
					case 27:
						var a = n.stateNode;
						Yc(e, qc(e), a);
						break;
					case 5:
						var o = n.stateNode;
						n.flags & 32 && (Xt(o, ""), n.flags &= -33), Yc(e, qc(e), o);
						break;
					case 3:
					case 4:
						var s = n.stateNode.containerInfo;
						Jc(e, qc(e), s);
						break;
					default: throw Error(i(161));
				}
			} catch (t) {
				Q(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function _l(e) {
		if (e.subtreeFlags & 1024) for (e = e.child; e !== null;) {
			var t = e;
			_l(t), t.tag === 5 && t.flags & 1024 && t.stateNode.reset(), e = e.sibling;
		}
	}
	function vl(e, t) {
		if (t.subtreeFlags & 8772) for (t = t.child; t !== null;) rl(e, t.alternate, t), t = t.sibling;
	}
	function yl(e) {
		for (e = e.child; e !== null;) {
			var t = e;
			switch (t.tag) {
				case 0:
				case 11:
				case 14:
				case 15:
					zc(4, t, t.return), yl(t);
					break;
				case 1:
					Uc(t, t.return);
					var n = t.stateNode;
					typeof n.componentWillUnmount == "function" && Vc(t, t.return, n), yl(t);
					break;
				case 27: pf(t.stateNode);
				case 26:
				case 5:
					Uc(t, t.return), yl(t);
					break;
				case 22:
					t.memoizedState === null && yl(t);
					break;
				case 30:
					yl(t);
					break;
				default: yl(t);
			}
			e = e.sibling;
		}
	}
	function bl(e, t, n) {
		for (n = n && !!(t.subtreeFlags & 8772), t = t.child; t !== null;) {
			var r = t.alternate, i = e, a = t, o = a.flags;
			switch (a.tag) {
				case 0:
				case 11:
				case 15:
					bl(i, a, n), Rc(4, a);
					break;
				case 1:
					if (bl(i, a, n), r = a, i = r.stateNode, typeof i.componentDidMount == "function") try {
						i.componentDidMount();
					} catch (e) {
						Q(r, r.return, e);
					}
					if (r = a, i = r.updateQueue, i !== null) {
						var s = r.stateNode;
						try {
							var c = i.shared.hiddenCallbacks;
							if (c !== null) for (i.shared.hiddenCallbacks = null, i = 0; i < c.length; i++) Ja(c[i], s);
						} catch (e) {
							Q(r, r.return, e);
						}
					}
					n && o & 64 && Bc(a), Hc(a, a.return);
					break;
				case 27: Xc(a);
				case 26:
				case 5:
					bl(i, a, n), n && r === null && o & 4 && Wc(a), Hc(a, a.return);
					break;
				case 12:
					bl(i, a, n);
					break;
				case 31:
					bl(i, a, n), n && o & 4 && ll(i, a);
					break;
				case 13:
					bl(i, a, n), n && o & 4 && ul(i, a);
					break;
				case 22:
					a.memoizedState === null && bl(i, a, n), Hc(a, a.return);
					break;
				case 30: break;
				default: bl(i, a, n);
			}
			t = t.sibling;
		}
	}
	function xl(e, t) {
		var n = null;
		e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== n && (e != null && e.refCount++, n != null && ua(n));
	}
	function Sl(e, t) {
		e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ua(e));
	}
	function Cl(e, t, n, r) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) wl(e, t, n, r), t = t.sibling;
	}
	function wl(e, t, n, r) {
		var i = t.flags;
		switch (t.tag) {
			case 0:
			case 11:
			case 15:
				Cl(e, t, n, r), i & 2048 && Rc(9, t);
				break;
			case 1:
				Cl(e, t, n, r);
				break;
			case 3:
				Cl(e, t, n, r), i & 2048 && (e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ua(e)));
				break;
			case 12:
				if (i & 2048) {
					Cl(e, t, n, r), e = t.stateNode;
					try {
						var a = t.memoizedProps, o = a.id, s = a.onPostCommit;
						typeof s == "function" && s(o, t.alternate === null ? "mount" : "update", e.passiveEffectDuration, -0);
					} catch (e) {
						Q(t, t.return, e);
					}
				} else Cl(e, t, n, r);
				break;
			case 31:
				Cl(e, t, n, r);
				break;
			case 13:
				Cl(e, t, n, r);
				break;
			case 23: break;
			case 22:
				a = t.stateNode, o = t.alternate, t.memoizedState === null ? a._visibility & 2 ? Cl(e, t, n, r) : (a._visibility |= 2, Tl(e, t, n, r, !!(t.subtreeFlags & 10256) || !1)) : a._visibility & 2 ? Cl(e, t, n, r) : El(e, t), i & 2048 && xl(o, t);
				break;
			case 24:
				Cl(e, t, n, r), i & 2048 && Sl(t.alternate, t);
				break;
			default: Cl(e, t, n, r);
		}
	}
	function Tl(e, t, n, r, i) {
		for (i = i && (!!(t.subtreeFlags & 10256) || !1), t = t.child; t !== null;) {
			var a = e, o = t, s = n, c = r, l = o.flags;
			switch (o.tag) {
				case 0:
				case 11:
				case 15:
					Tl(a, o, s, c, i), Rc(8, o);
					break;
				case 23: break;
				case 22:
					var u = o.stateNode;
					o.memoizedState === null ? (u._visibility |= 2, Tl(a, o, s, c, i)) : u._visibility & 2 ? Tl(a, o, s, c, i) : El(a, o), i && l & 2048 && xl(o.alternate, o);
					break;
				case 24:
					Tl(a, o, s, c, i), i && l & 2048 && Sl(o.alternate, o);
					break;
				default: Tl(a, o, s, c, i);
			}
			t = t.sibling;
		}
	}
	function El(e, t) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) {
			var n = e, r = t, i = r.flags;
			switch (r.tag) {
				case 22:
					El(n, r), i & 2048 && xl(r.alternate, r);
					break;
				case 24:
					El(n, r), i & 2048 && Sl(r.alternate, r);
					break;
				default: El(n, r);
			}
			t = t.sibling;
		}
	}
	var Dl = 8192;
	function Ol(e, t, n) {
		if (e.subtreeFlags & Dl) for (e = e.child; e !== null;) kl(e, t, n), e = e.sibling;
	}
	function kl(e, t, n) {
		switch (e.tag) {
			case 26:
				Ol(e, t, n), e.flags & Dl && e.memoizedState !== null && Gf(n, ml, e.memoizedState, e.memoizedProps);
				break;
			case 5:
				Ol(e, t, n);
				break;
			case 3:
			case 4:
				var r = ml;
				ml = gf(e.stateNode.containerInfo), Ol(e, t, n), ml = r;
				break;
			case 22:
				e.memoizedState === null && (r = e.alternate, r !== null && r.memoizedState !== null ? (r = Dl, Dl = 16777216, Ol(e, t, n), Dl = r) : Ol(e, t, n));
				break;
			default: Ol(e, t, n);
		}
	}
	function Al(e) {
		var t = e.alternate;
		if (t !== null && (e = t.child, e !== null)) {
			t.child = null;
			do
				t = e.sibling, e.sibling = null, e = t;
			while (e !== null);
		}
	}
	function jl(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				tl = r, Pl(r, e);
			}
			Al(e);
		}
		if (e.subtreeFlags & 10256) for (e = e.child; e !== null;) Ml(e), e = e.sibling;
	}
	function Ml(e) {
		switch (e.tag) {
			case 0:
			case 11:
			case 15:
				jl(e), e.flags & 2048 && zc(9, e, e.return);
				break;
			case 3:
				jl(e);
				break;
			case 12:
				jl(e);
				break;
			case 22:
				var t = e.stateNode;
				e.memoizedState !== null && t._visibility & 2 && (e.return === null || e.return.tag !== 13) ? (t._visibility &= -3, Nl(e)) : jl(e);
				break;
			default: jl(e);
		}
	}
	function Nl(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				tl = r, Pl(r, e);
			}
			Al(e);
		}
		for (e = e.child; e !== null;) {
			switch (t = e, t.tag) {
				case 0:
				case 11:
				case 15:
					zc(8, t, t.return), Nl(t);
					break;
				case 22:
					n = t.stateNode, n._visibility & 2 && (n._visibility &= -3, Nl(t));
					break;
				default: Nl(t);
			}
			e = e.sibling;
		}
	}
	function Pl(e, t) {
		for (; tl !== null;) {
			var n = tl;
			switch (n.tag) {
				case 0:
				case 11:
				case 15:
					zc(8, n, t);
					break;
				case 23:
				case 22:
					if (n.memoizedState !== null && n.memoizedState.cachePool !== null) {
						var r = n.memoizedState.cachePool.pool;
						r != null && r.refCount++;
					}
					break;
				case 24: ua(n.memoizedState.cache);
			}
			if (r = n.child, r !== null) r.return = n, tl = r;
			else a: for (n = e; tl !== null;) {
				r = tl;
				var i = r.sibling, a = r.return;
				if (il(r), r === n) {
					tl = null;
					break a;
				}
				if (i !== null) {
					i.return = a, tl = i;
					break a;
				}
				tl = a;
			}
		}
	}
	var Fl = {
		getCacheForType: function(e) {
			var t = R(ca), n = t.data.get(e);
			return n === void 0 && (n = e(), t.data.set(e, n)), n;
		},
		cacheSignal: function() {
			return R(ca).controller.signal;
		}
	}, Il = typeof WeakMap == "function" ? WeakMap : Map, J = 0, Ll = null, Y = null, X = 0, Z = 0, Rl = null, zl = !1, Bl = !1, Vl = !1, Hl = 0, Ul = 0, Wl = 0, Gl = 0, Kl = 0, ql = 0, Jl = 0, Yl = null, Xl = null, Zl = !1, Ql = 0, $l = 0, eu = Infinity, tu = null, nu = null, ru = 0, iu = null, au = null, ou = 0, su = 0, cu = null, lu = null, uu = 0, du = null;
	function fu() {
		return J & 2 && X !== 0 ? X & -X : A.T === null ? lt() : ud();
	}
	function pu() {
		if (ql === 0) {
			if (!(X & 536870912) || L) {
				var e = Je;
				Je <<= 1, !(Je & 3932160) && (Je = 262144), ql = e;
			} else ql = 536870912;
		}
		return e = Za.current, e !== null && (e.flags |= 32), ql;
	}
	function mu(e, t, n) {
		(e === Ll && (Z === 2 || Z === 9) || e.cancelPendingCommit !== null) && (xu(e, 0), vu(e, X, ql, !1)), nt(e, n), (!(J & 2) || e !== Ll) && (e === Ll && (!(J & 2) && (Gl |= n), Ul === 4 && vu(e, X, ql, !1)), nd(e));
	}
	function hu(e, t, n) {
		if (J & 6) throw Error(i(327));
		var r = !n && !(t & 127) && (t & e.expiredLanes) === 0 || Qe(e, t), a = r ? ku(e, t) : Du(e, t, !0), o = r;
		do {
			if (a === 0) {
				Bl && !r && vu(e, t, 0, !1);
				break;
			}
			if (n = e.current.alternate, o && !_u(n)) {
				a = Du(e, t, !1), o = !1;
				continue;
			}
			if (a === 2) {
				if (o = t, e.errorRecoveryDisabledLanes & o) var s = 0;
				else s = e.pendingLanes & -536870913, s = s === 0 ? s & 536870912 ? 536870912 : 0 : s;
				if (s !== 0) {
					t = s;
					a: {
						var c = e;
						a = Yl;
						var l = c.current.memoizedState.isDehydrated;
						if (l && (xu(c, s).flags |= 256), s = Du(c, s, !1), s !== 2) {
							if (Vl && !l) {
								c.errorRecoveryDisabledLanes |= o, Gl |= o, a = 4;
								break a;
							}
							o = Xl, Xl = a, o !== null && (Xl === null ? Xl = o : Xl.push.apply(Xl, o));
						}
						a = s;
					}
					if (o = !1, a !== 2) continue;
				}
			}
			if (a === 1) {
				xu(e, 0), vu(e, t, 0, !0);
				break;
			}
			a: {
				switch (r = e, o = a, o) {
					case 0:
					case 1: throw Error(i(345));
					case 4: if ((t & 4194048) !== t) break;
					case 6:
						vu(r, t, ql, !zl);
						break a;
					case 2:
						Xl = null;
						break;
					case 3:
					case 5: break;
					default: throw Error(i(329));
				}
				if ((t & 62914560) === t && (a = Ql + 300 - je(), 10 < a)) {
					if (vu(r, t, ql, !zl), Ze(r, 0, !0) !== 0) break a;
					ou = t, r.timeoutHandle = Kd(gu.bind(null, r, n, Xl, tu, Zl, t, ql, Gl, Jl, zl, o, "Throttled", -0, 0), a);
					break a;
				}
				gu(r, n, Xl, tu, Zl, t, ql, Gl, Jl, zl, o, null, -0, 0);
			}
			break;
		} while (1);
		nd(e);
	}
	function gu(e, t, n, r, i, a, o, s, c, l, u, d, f, p) {
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
			}, kl(t, a, d);
			var m = (a & 62914560) === a ? Ql - je() : (a & 4194048) === a ? $l - je() : 0;
			if (m = qf(d, m), m !== null) {
				ou = a, e.cancelPendingCommit = m(Iu.bind(null, e, t, a, n, r, i, o, s, c, u, d, null, f, p)), vu(e, a, o, !l);
				return;
			}
		}
		Iu(e, t, a, n, r, i, o, s, c);
	}
	function _u(e) {
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
	function vu(e, t, n, r) {
		t &= ~Kl, t &= ~Gl, e.suspendedLanes |= t, e.pingedLanes &= ~t, r && (e.warmLanes |= t), r = e.expirationTimes;
		for (var i = t; 0 < i;) {
			var a = 31 - Ue(i), o = 1 << a;
			r[a] = -1, i &= ~o;
		}
		n !== 0 && it(e, n, t);
	}
	function yu() {
		return J & 6 ? !0 : (rd(0, !1), !1);
	}
	function bu() {
		if (Y !== null) {
			if (Z === 0) var e = Y.return;
			else e = Y, Yi = Ji = null, wo(e), Na = null, Pa = 0, e = Y;
			for (; e !== null;) Lc(e.alternate, e), e = e.return;
			Y = null;
		}
	}
	function xu(e, t) {
		var n = e.timeoutHandle;
		n !== -1 && (e.timeoutHandle = -1, qd(n)), n = e.cancelPendingCommit, n !== null && (e.cancelPendingCommit = null, n()), ou = 0, bu(), Ll = e, Y = n = fi(e.current, null), X = t, Z = 0, Rl = null, zl = !1, Bl = Qe(e, t), Vl = !1, Jl = ql = Kl = Gl = Wl = Ul = 0, Xl = Yl = null, Zl = !1, t & 8 && (t |= t & 32);
		var r = e.entangledLanes;
		if (r !== 0) for (e = e.entanglements, r &= t; 0 < r;) {
			var i = 31 - Ue(r), a = 1 << i;
			t |= e[i], r &= ~a;
		}
		return Hl = t, ni(), n;
	}
	function Su(e, t) {
		K = null, A.H = Ps, t === Ca || t === Ta ? (t = ja(), Z = 3) : t === wa ? (t = ja(), Z = 4) : Z = t === Qs ? 8 : typeof t == "object" && t && typeof t.then == "function" ? 6 : 1, Rl = t, Y === null && (Ul = 1, Ks(e, bi(t, e.current)));
	}
	function Cu() {
		var e = Za.current;
		return e === null ? !0 : (X & 4194048) === X ? Qa === null : (X & 62914560) === X || X & 536870912 ? e === Qa : !1;
	}
	function wu() {
		var e = A.H;
		return A.H = Ps, e === null ? Ps : e;
	}
	function Tu() {
		var e = A.A;
		return A.A = Fl, e;
	}
	function Eu() {
		Ul = 4, zl || (X & 4194048) !== X && Za.current !== null || (Bl = !0), !(Wl & 134217727) && !(Gl & 134217727) || Ll === null || vu(Ll, X, ql, !1);
	}
	function Du(e, t, n) {
		var r = J;
		J |= 2;
		var i = wu(), a = Tu();
		(Ll !== e || X !== t) && (tu = null, xu(e, t)), t = !1;
		var o = Ul;
		a: do
			try {
				if (Z !== 0 && Y !== null) {
					var s = Y, c = Rl;
					switch (Z) {
						case 8:
							bu(), o = 6;
							break a;
						case 3:
						case 2:
						case 9:
						case 6:
							Za.current === null && (t = !0);
							var l = Z;
							if (Z = 0, Rl = null, Nu(e, s, c, l), n && Bl) {
								o = 0;
								break a;
							}
							break;
						default: l = Z, Z = 0, Rl = null, Nu(e, s, c, l);
					}
				}
				Ou(), o = Ul;
				break;
			} catch (t) {
				Su(e, t);
			}
		while (1);
		return t && e.shellSuspendCounter++, Yi = Ji = null, J = r, A.H = i, A.A = a, Y === null && (Ll = null, X = 0, ni()), o;
	}
	function Ou() {
		for (; Y !== null;) ju(Y);
	}
	function ku(e, t) {
		var n = J;
		J |= 2;
		var r = wu(), a = Tu();
		Ll !== e || X !== t ? (tu = null, eu = je() + 500, xu(e, t)) : Bl = Qe(e, t);
		a: do
			try {
				if (Z !== 0 && Y !== null) {
					t = Y;
					var o = Rl;
					b: switch (Z) {
						case 1:
							Z = 0, Rl = null, Nu(e, t, o, 1);
							break;
						case 2:
						case 9:
							if (Da(o)) {
								Z = 0, Rl = null, Mu(t);
								break;
							}
							t = function() {
								Z !== 2 && Z !== 9 || Ll !== e || (Z = 7), nd(e);
							}, o.then(t, t);
							break a;
						case 3:
							Z = 7;
							break a;
						case 4:
							Z = 5;
							break a;
						case 7:
							Da(o) ? (Z = 0, Rl = null, Mu(t)) : (Z = 0, Rl = null, Nu(e, t, o, 7));
							break;
						case 5:
							var s = null;
							switch (Y.tag) {
								case 26: s = Y.memoizedState;
								case 5:
								case 27:
									var c = Y;
									if (s ? Wf(s) : c.stateNode.complete) {
										Z = 0, Rl = null;
										var l = c.sibling;
										if (l !== null) Y = l;
										else {
											var u = c.return;
											u === null ? Y = null : (Y = u, Pu(u));
										}
										break b;
									}
							}
							Z = 0, Rl = null, Nu(e, t, o, 5);
							break;
						case 6:
							Z = 0, Rl = null, Nu(e, t, o, 6);
							break;
						case 8:
							bu(), Ul = 6;
							break a;
						default: throw Error(i(462));
					}
				}
				Au();
				break;
			} catch (t) {
				Su(e, t);
			}
		while (1);
		return Yi = Ji = null, A.H = r, A.A = a, J = n, Y === null ? (Ll = null, X = 0, ni(), Ul) : 0;
	}
	function Au() {
		for (; Y !== null && !ke();) ju(Y);
	}
	function ju(e) {
		var t = Oc(e.alternate, e, Hl);
		e.memoizedProps = e.pendingProps, t === null ? Pu(e) : Y = t;
	}
	function Mu(e) {
		var t = e, n = t.alternate;
		switch (t.tag) {
			case 15:
			case 0:
				t = fc(n, t, t.pendingProps, t.type, void 0, X);
				break;
			case 11:
				t = fc(n, t, t.pendingProps, t.type.render, t.ref, X);
				break;
			case 5: wo(t);
			default: Lc(n, t), t = Y = pi(t, Hl), t = Oc(n, t, Hl);
		}
		e.memoizedProps = e.pendingProps, t === null ? Pu(e) : Y = t;
	}
	function Nu(e, t, n, r) {
		Yi = Ji = null, wo(t), Na = null, Pa = 0;
		var i = t.return;
		try {
			if (Zs(e, i, t, n, X)) {
				Ul = 1, Ks(e, bi(n, e.current)), Y = null;
				return;
			}
		} catch (t) {
			if (i !== null) throw Y = i, t;
			Ul = 1, Ks(e, bi(n, e.current)), Y = null;
			return;
		}
		t.flags & 32768 ? (L || r === 1 ? e = !0 : Bl || X & 536870912 ? e = !1 : (zl = e = !0, (r === 2 || r === 9 || r === 3 || r === 6) && (r = Za.current, r !== null && r.tag === 13 && (r.flags |= 16384))), Fu(t, e)) : Pu(t);
	}
	function Pu(e) {
		var t = e;
		do {
			if (t.flags & 32768) {
				Fu(t, zl);
				return;
			}
			e = t.return;
			var n = Fc(t.alternate, t, Hl);
			if (n !== null) {
				Y = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				Y = t;
				return;
			}
			Y = t = e;
		} while (t !== null);
		Ul === 0 && (Ul = 5);
	}
	function Fu(e, t) {
		do {
			var n = Ic(e.alternate, e);
			if (n !== null) {
				n.flags &= 32767, Y = n;
				return;
			}
			if (n = e.return, n !== null && (n.flags |= 32768, n.subtreeFlags = 0, n.deletions = null), !t && (e = e.sibling, e !== null)) {
				Y = e;
				return;
			}
			Y = e = n;
		} while (e !== null);
		Ul = 6, Y = null;
	}
	function Iu(e, t, n, r, a, o, s, c, l) {
		e.cancelPendingCommit = null;
		do
			Vu();
		while (ru !== 0);
		if (J & 6) throw Error(i(327));
		if (t !== null) {
			if (t === e.current) throw Error(i(177));
			if (o = t.lanes | t.childLanes, o |= ti, rt(e, n, o, s, c, l), e === Ll && (Y = Ll = null, X = 0), au = t, iu = e, ou = n, su = o, cu = a, lu = r, t.subtreeFlags & 10256 || t.flags & 10256 ? (e.callbackNode = null, e.callbackPriority = 0, Yu(Fe, function() {
				return Hu(), null;
			})) : (e.callbackNode = null, e.callbackPriority = 0), r = !!(t.flags & 13878), t.subtreeFlags & 13878 || r) {
				r = A.T, A.T = null, a = j.p, j.p = 2, s = J, J |= 4;
				try {
					nl(e, t, n);
				} finally {
					J = s, j.p = a, A.T = r;
				}
			}
			ru = 1, Lu(), Ru(), zu();
		}
	}
	function Lu() {
		if (ru === 1) {
			ru = 0;
			var e = iu, t = au, n = !!(t.flags & 13878);
			if (t.subtreeFlags & 13878 || n) {
				n = A.T, A.T = null;
				var r = j.p;
				j.p = 2;
				var i = J;
				J |= 4;
				try {
					hl(t, e);
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
					J = i, j.p = r, A.T = n;
				}
			}
			e.current = t, ru = 2;
		}
	}
	function Ru() {
		if (ru === 2) {
			ru = 0;
			var e = iu, t = au, n = !!(t.flags & 8772);
			if (t.subtreeFlags & 8772 || n) {
				n = A.T, A.T = null;
				var r = j.p;
				j.p = 2;
				var i = J;
				J |= 4;
				try {
					rl(e, t.alternate, t);
				} finally {
					J = i, j.p = r, A.T = n;
				}
			}
			ru = 3;
		}
	}
	function zu() {
		if (ru === 4 || ru === 3) {
			ru = 0, Ae();
			var e = iu, t = au, n = ou, r = lu;
			t.subtreeFlags & 10256 || t.flags & 10256 ? ru = 5 : (ru = 0, au = iu = null, Bu(e, e.pendingLanes));
			var i = e.pendingLanes;
			if (i === 0 && (nu = null), ct(n), t = t.stateNode, Ve && typeof Ve.onCommitFiberRoot == "function") try {
				Ve.onCommitFiberRoot(Be, t, void 0, (t.current.flags & 128) == 128);
			} catch {}
			if (r !== null) {
				t = A.T, i = j.p, j.p = 2, A.T = null;
				try {
					for (var a = e.onRecoverableError, o = 0; o < r.length; o++) {
						var s = r[o];
						a(s.value, { componentStack: s.stack });
					}
				} finally {
					A.T = t, j.p = i;
				}
			}
			ou & 3 && Vu(), nd(e), i = e.pendingLanes, n & 261930 && i & 42 ? e === du ? uu++ : (uu = 0, du = e) : uu = 0, rd(0, !1);
		}
	}
	function Bu(e, t) {
		(e.pooledCacheLanes &= t) === 0 && (t = e.pooledCache, t != null && (e.pooledCache = null, ua(t)));
	}
	function Vu() {
		return Lu(), Ru(), zu(), Hu();
	}
	function Hu() {
		if (ru !== 5) return !1;
		var e = iu, t = su;
		su = 0;
		var n = ct(ou), r = A.T, a = j.p;
		try {
			j.p = 32 > n ? 32 : n, A.T = null, n = cu, cu = null;
			var o = iu, s = ou;
			if (ru = 0, au = iu = null, ou = 0, J & 6) throw Error(i(331));
			var c = J;
			if (J |= 4, Ml(o.current), wl(o, o.current, s, n), J = c, rd(0, !1), Ve && typeof Ve.onPostCommitFiberRoot == "function") try {
				Ve.onPostCommitFiberRoot(Be, o);
			} catch {}
			return !0;
		} finally {
			j.p = a, A.T = r, Bu(e, t);
		}
	}
	function Uu(e, t, n) {
		t = bi(n, t), t = Js(e.stateNode, t, 2), e = Ua(e, t, 2), e !== null && (nt(e, 2), nd(e));
	}
	function Q(e, t, n) {
		if (e.tag === 3) Uu(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Uu(t, e, n);
				break;
			}
			if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (nu === null || !nu.has(r))) {
					e = bi(n, e), n = Ys(2), r = Ua(t, n, 2), r !== null && (Xs(n, r, t, e), nt(r, 2), nd(r));
					break;
				}
			}
			t = t.return;
		}
	}
	function Wu(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Il();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (Vl = !0, i.add(n), e = Gu.bind(null, e, t, n), t.then(e, e));
	}
	function Gu(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), e.pingedLanes |= e.suspendedLanes & n, e.warmLanes &= ~n, Ll === e && (X & n) === n && (Ul === 4 || Ul === 3 && (X & 62914560) === X && 300 > je() - Ql ? !(J & 2) && xu(e, 0) : Kl |= n, Jl === X && (Jl = 0)), nd(e);
	}
	function Ku(e, t) {
		t === 0 && (t = et()), e = ai(e, t), e !== null && (nt(e, t), nd(e));
	}
	function qu(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), Ku(e, n);
	}
	function Ju(e, t) {
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
		r !== null && r.delete(t), Ku(e, n);
	}
	function Yu(e, t) {
		return De(e, t);
	}
	var Xu = null, Zu = null, Qu = !1, $u = !1, ed = !1, td = 0;
	function nd(e) {
		e !== Zu && e.next === null && (Zu === null ? Xu = Zu = e : Zu = Zu.next = e), $u = !0, Qu || (Qu = !0, ld());
	}
	function rd(e, t) {
		if (!ed && $u) {
			ed = !0;
			do
				for (var n = !1, r = Xu; r !== null;) {
					if (!t) {
						if (e !== 0) {
							var i = r.pendingLanes;
							if (i === 0) var a = 0;
							else {
								var o = r.suspendedLanes, s = r.pingedLanes;
								a = (1 << 31 - Ue(42 | e) + 1) - 1, a &= i & ~(o & ~s), a = a & 201326741 ? a & 201326741 | 1 : a ? a | 2 : 0;
							}
							a !== 0 && (n = !0, cd(r, a));
						} else a = X, a = Ze(r, r === Ll ? a : 0, r.cancelPendingCommit !== null || r.timeoutHandle !== -1), !(a & 3) || Qe(r, a) || (n = !0, cd(r, a));
					}
					r = r.next;
				}
			while (n);
			ed = !1;
		}
	}
	function id() {
		ad();
	}
	function ad() {
		$u = Qu = !1;
		var e = 0;
		td !== 0 && Gd() && (e = td);
		for (var t = je(), n = null, r = Xu; r !== null;) {
			var i = r.next, a = od(r, t);
			a === 0 ? (r.next = null, n === null ? Xu = i : n.next = i, i === null && (Zu = n)) : (n = r, (e !== 0 || a & 3) && ($u = !0)), r = i;
		}
		ru !== 0 && ru !== 5 || rd(e, !1), td !== 0 && (td = 0);
	}
	function od(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes & -62914561; 0 < a;) {
			var o = 31 - Ue(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = $e(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
		if (t = Ll, n = X, n = Ze(e, e === t ? n : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r = e.callbackNode, n === 0 || e === t && (Z === 2 || Z === 9) || e.cancelPendingCommit !== null) return r !== null && r !== null && Oe(r), e.callbackNode = null, e.callbackPriority = 0;
		if (!(n & 3) || Qe(e, n)) {
			if (t = n & -n, t === e.callbackPriority) return t;
			switch (r !== null && Oe(r), ct(n)) {
				case 2:
				case 8:
					n = Pe;
					break;
				case 32:
					n = Fe;
					break;
				case 268435456:
					n = Le;
					break;
				default: n = Fe;
			}
			return r = sd.bind(null, e), n = De(n, r), e.callbackPriority = t, e.callbackNode = n, t;
		}
		return r !== null && r !== null && Oe(r), e.callbackPriority = 2, e.callbackNode = null, 2;
	}
	function sd(e, t) {
		if (ru !== 0 && ru !== 5) return e.callbackNode = null, e.callbackPriority = 0, null;
		var n = e.callbackNode;
		if (Vu() && e.callbackNode !== n) return null;
		var r = X;
		return r = Ze(e, e === Ll ? r : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r === 0 ? null : (hu(e, r, t), od(e, je()), e.callbackNode != null && e.callbackNode === n ? sd.bind(null, e) : null);
	}
	function cd(e, t) {
		if (Vu()) return null;
		hu(e, t, !0);
	}
	function ld() {
		Yd(function() {
			J & 6 ? De(Ne, id) : ad();
		});
	}
	function ud() {
		if (td === 0) {
			var e = pa;
			e === 0 && (e = qe, qe <<= 1, !(qe & 261888) && (qe = 256)), td = e;
		}
		return td;
	}
	function dd(e) {
		return e == null || typeof e == "symbol" || typeof e == "boolean" ? null : typeof e == "function" ? e : rn("" + e);
	}
	function fd(e, t) {
		var n = t.ownerDocument.createElement("input");
		return n.name = t.name, n.value = t.value, e.id && n.setAttribute("form", e.id), t.parentNode.insertBefore(n, t), e = new FormData(e), n.parentNode.removeChild(n), e;
	}
	function pd(e, t, n, r, i) {
		if (t === "submit" && n && n.stateNode === i) {
			var a = dd((i[pt] || null).action), o = r.submitter;
			o && (t = (t = o[pt] || null) ? dd(t.formAction) : o.getAttribute("formAction"), t !== null && (a = t, o = null));
			var s = new En("action", "action", null, r, i);
			e.push({
				event: s,
				listeners: [{
					instance: null,
					listener: function() {
						if (r.defaultPrevented) {
							if (td !== 0) {
								var e = o ? fd(i, o) : new FormData(i);
								bs(n, {
									pending: !0,
									data: e,
									method: i.method,
									action: a
								}, null, e);
							}
						} else typeof a == "function" && (s.preventDefault(), e = o ? fd(i, o) : new FormData(i), bs(n, {
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
	for (var md = 0; md < Xr.length; md++) {
		var hd = Xr[md];
		Zr(hd.toLowerCase(), "on" + (hd[0].toUpperCase() + hd.slice(1)));
	}
	Zr(Hr, "onAnimationEnd"), Zr(Ur, "onAnimationIteration"), Zr(Wr, "onAnimationStart"), Zr("dblclick", "onDoubleClick"), Zr("focusin", "onFocus"), Zr("focusout", "onBlur"), Zr(Gr, "onTransitionRun"), Zr(Kr, "onTransitionStart"), Zr(qr, "onTransitionCancel"), Zr(Jr, "onTransitionEnd"), kt("onMouseEnter", ["mouseout", "mouseover"]), kt("onMouseLeave", ["mouseout", "mouseover"]), kt("onPointerEnter", ["pointerout", "pointerover"]), kt("onPointerLeave", ["pointerout", "pointerover"]), Ot("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), Ot("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), Ot("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), Ot("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), Ot("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), Ot("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
	var gd = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), _d = new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(gd));
	function vd(e, t) {
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
	function $(e, t) {
		var n = t[ht];
		n === void 0 && (n = t[ht] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (Sd(t, e, 2, !1), n.add(r));
	}
	function yd(e, t, n) {
		var r = 0;
		t && (r |= 4), Sd(n, e, r, t);
	}
	var bd = "_reactListening" + Math.random().toString(36).slice(2);
	function xd(e) {
		if (!e[bd]) {
			e[bd] = !0, Et.forEach(function(t) {
				t !== "selectionchange" && (_d.has(t) || yd(t, !1, e), yd(t, !0, e));
			});
			var t = e.nodeType === 9 ? e : e.ownerDocument;
			t === null || t[bd] || (t[bd] = !0, yd("selectionchange", !1, t));
		}
	}
	function Sd(e, t, n, r) {
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
	function Cd(e, t, n, r, i) {
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
					if (s = xt(c), s === null) return;
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
							u = "focus", l = Fn;
							break;
						case "focusout":
							u = "blur", l = Fn;
							break;
						case "beforeblur":
						case "afterblur":
							l = Fn;
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
							l = P;
							break;
						case Jr:
							l = Kn;
							break;
						case "scroll":
						case "scrollend":
							l = On;
							break;
						case "wheel":
							l = qn;
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
						case "beforetoggle": l = F;
					}
					var d = !!(t & 4), f = !d && (e === "scroll" || e === "scrollend"), p = d ? c === null ? null : c + "Capture" : c;
					d = [];
					for (var m = r, h; m !== null;) {
						var g = m;
						if (h = g.stateNode, g = g.tag, g !== 5 && g !== 26 && g !== 27 || h === null || p === null || (g = pn(m, p), g != null && d.push(wd(m, g, h))), f) break;
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
					if (c = e === "mouseover" || e === "pointerover", l = e === "mouseout" || e === "pointerout", c && n !== on && (u = n.relatedTarget || n.fromElement) && (xt(u) || u[mt])) break a;
					if ((l || c) && (c = i.window === i ? i : (c = i.ownerDocument) ? c.defaultView || c.parentWindow : window, l ? (u = n.relatedTarget || n.toElement, l = r, u = u ? xt(u) : null, u !== null && (f = o(u), d = u.tag, u !== f || d !== 5 && d !== 27 && d !== 6) && (u = null)) : (l = null, u = r), l !== u)) {
						if (d = Nn, g = "onMouseLeave", p = "onMouseEnter", m = "mouse", (e === "pointerout" || e === "pointerover") && (d = Wn, g = "onPointerLeave", p = "onPointerEnter", m = "pointer"), f = l == null ? c : Ct(l), h = u == null ? c : Ct(u), c = new d(g, m + "leave", l, n, i), c.target = f, c.relatedTarget = h, g = null, xt(i) === r && (d = new d(p, m + "enter", u, n, i), d.target = h, d.relatedTarget = f, g = d), f = g, l && u) b: {
							for (d = Ed, p = l, m = u, h = 0, g = p; g; g = d(g)) h++;
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
						l !== null && Dd(s, c, l, d, !1), u !== null && f !== null && Dd(s, f, u, d, !0);
					}
				}
				a: {
					if (c = r ? Ct(r) : window, l = c.nodeName && c.nodeName.toLowerCase(), l === "select" || l === "input" && c.type === "file") var v = fr;
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
					y && y(e, c, r), e === "focusout" && r && c.type === "number" && r.memoizedProps.value != null && qt(c, "number", c.value);
				}
				switch (y = r ? Ct(r) : window, e) {
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
				x && (Qn && n.locale !== "ko" && (rr || x !== "onCompositionStart" ? x === "onCompositionEnd" && rr && (b = bn()) : (_n = i, vn = "value" in _n ? _n.value : _n.textContent, rr = !0)), y = Td(r, x), 0 < y.length && (x = new Ln(x, e, null, n, i), s.push({
					event: x,
					listeners: y
				}), b ? x.data = b : (b = nr(n), b !== null && (x.data = b)))), (b = Zn ? ir(e, n) : ar(e, n)) && (x = Td(r, "onBeforeInput"), 0 < x.length && (y = new Ln("onBeforeInput", "beforeinput", null, n, i), s.push({
					event: y,
					listeners: x
				}), y.data = b)), pd(s, e, r, n, i);
			}
			vd(s, t);
		});
	}
	function wd(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function Td(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			if (i = i.tag, i !== 5 && i !== 26 && i !== 27 || a === null || (i = pn(e, n), i != null && r.unshift(wd(e, i, a)), i = pn(e, t), i != null && r.push(wd(e, i, a))), e.tag === 3) return r;
			e = e.return;
		}
		return [];
	}
	function Ed(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5 && e.tag !== 27);
		return e || null;
	}
	function Dd(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (s = s.tag, c !== null && c === r) break;
			s !== 5 && s !== 26 && s !== 27 || l === null || (c = l, i ? (l = pn(n, a), l != null && o.unshift(wd(n, l, c))) : i || (l = pn(n, a), l != null && o.push(wd(n, l, c)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var Od = /\r\n?/g, kd = /\u0000|\uFFFD/g;
	function Ad(e) {
		return (typeof e == "string" ? e : "" + e).replace(Od, "\n").replace(kd, "");
	}
	function jd(e, t) {
		return t = Ad(t), Ad(e) === t;
	}
	function Md(e, t, n, r, a, o) {
		switch (n) {
			case "children":
				typeof r == "string" ? t === "body" || t === "textarea" && r === "" || Xt(e, r) : (typeof r == "number" || typeof r == "bigint") && t !== "body" && Xt(e, "" + r);
				break;
			case "className":
				Ft(e, "class", r);
				break;
			case "tabIndex":
				Ft(e, "tabindex", r);
				break;
			case "dir":
			case "role":
			case "viewBox":
			case "width":
			case "height":
				Ft(e, n, r);
				break;
			case "style":
				$t(e, r, o);
				break;
			case "data": if (t !== "object") {
				Ft(e, "data", r);
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
				if (typeof o == "function" && (n === "formAction" ? (t !== "input" && Md(e, t, "name", a.name, a, null), Md(e, t, "formEncType", a.formEncType, a, null), Md(e, t, "formMethod", a.formMethod, a, null), Md(e, t, "formTarget", a.formTarget, a, null)) : (Md(e, t, "encType", a.encType, a, null), Md(e, t, "method", a.method, a, null), Md(e, t, "target", a.target, a, null))), r == null || typeof r == "symbol" || typeof r == "boolean") {
					e.removeAttribute(n);
					break;
				}
				r = rn("" + r), e.setAttribute(n, r);
				break;
			case "onClick":
				r != null && (e.onclick = an);
				break;
			case "onScroll":
				r != null && $("scroll", e);
				break;
			case "onScrollEnd":
				r != null && $("scrollend", e);
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
				$("beforetoggle", e), $("toggle", e), Pt(e, "popover", r);
				break;
			case "xlinkActuate":
				It(e, "http://www.w3.org/1999/xlink", "xlink:actuate", r);
				break;
			case "xlinkArcrole":
				It(e, "http://www.w3.org/1999/xlink", "xlink:arcrole", r);
				break;
			case "xlinkRole":
				It(e, "http://www.w3.org/1999/xlink", "xlink:role", r);
				break;
			case "xlinkShow":
				It(e, "http://www.w3.org/1999/xlink", "xlink:show", r);
				break;
			case "xlinkTitle":
				It(e, "http://www.w3.org/1999/xlink", "xlink:title", r);
				break;
			case "xlinkType":
				It(e, "http://www.w3.org/1999/xlink", "xlink:type", r);
				break;
			case "xmlBase":
				It(e, "http://www.w3.org/XML/1998/namespace", "xml:base", r);
				break;
			case "xmlLang":
				It(e, "http://www.w3.org/XML/1998/namespace", "xml:lang", r);
				break;
			case "xmlSpace":
				It(e, "http://www.w3.org/XML/1998/namespace", "xml:space", r);
				break;
			case "is":
				Pt(e, "is", r);
				break;
			case "innerText":
			case "textContent": break;
			default: (!(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (n = tn.get(n) || n, Pt(e, n, r));
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
				r != null && $("scroll", e);
				break;
			case "onScrollEnd":
				r != null && $("scrollend", e);
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
			default: if (!Dt.hasOwnProperty(n)) a: {
				if (n[0] === "o" && n[1] === "n" && (a = n.endsWith("Capture"), t = n.slice(2, a ? n.length - 7 : void 0), o = e[pt] || null, o = o == null ? null : o[n], typeof o == "function" && e.removeEventListener(t, o, a), typeof r == "function")) {
					typeof o != "function" && o !== null && (n in e ? e[n] = null : e.hasAttribute(n) && e.removeAttribute(n)), e.addEventListener(t, r, a);
					break a;
				}
				n in e ? e[n] = r : !0 === r ? e.setAttribute(n, "") : Pt(e, n, r);
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
				$("error", e), $("load", e);
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
						default: Md(e, t, o, s, n, null);
					}
				}
				a && Md(e, t, "srcSet", n.srcSet, n, null), r && Md(e, t, "src", n.src, n, null);
				return;
			case "input":
				$("invalid", e);
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
						default: Md(e, t, r, d, n, null);
					}
				}
				Kt(e, o, c, l, u, s, a, !1);
				return;
			case "select":
				for (a in $("invalid", e), r = s = o = null, n) if (n.hasOwnProperty(a) && (c = n[a], c != null)) switch (a) {
					case "value":
						o = c;
						break;
					case "defaultValue":
						s = c;
						break;
					case "multiple": r = c;
					default: Md(e, t, a, c, n, null);
				}
				t = o, n = s, e.multiple = !!r, t == null ? n != null && N(e, !!r, n, !0) : N(e, !!r, t, !1);
				return;
			case "textarea":
				for (s in $("invalid", e), o = a = r = null, n) if (n.hasOwnProperty(s) && (c = n[s], c != null)) switch (s) {
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
					default: Md(e, t, s, c, n, null);
				}
				Yt(e, r, a, o);
				return;
			case "option":
				for (l in n) if (n.hasOwnProperty(l) && (r = n[l], r != null)) switch (l) {
					case "selected":
						e.selected = r && typeof r != "function" && typeof r != "symbol";
						break;
					default: Md(e, t, l, r, n, null);
				}
				return;
			case "dialog":
				$("beforetoggle", e), $("toggle", e), $("cancel", e), $("close", e);
				break;
			case "iframe":
			case "object":
				$("load", e);
				break;
			case "video":
			case "audio":
				for (r = 0; r < gd.length; r++) $(gd[r], e);
				break;
			case "image":
				$("error", e), $("load", e);
				break;
			case "details":
				$("toggle", e);
				break;
			case "embed":
			case "source":
			case "link": $("error", e), $("load", e);
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
					default: Md(e, t, u, r, n, null);
				}
				return;
			default: if (en(t)) {
				for (d in n) n.hasOwnProperty(d) && (r = n[d], r !== void 0 && Nd(e, t, d, r, n, void 0));
				return;
			}
		}
		for (c in n) n.hasOwnProperty(c) && (r = n[c], r != null && Md(e, t, c, r, n, null));
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
						default: r.hasOwnProperty(m) || Md(e, t, m, null, r, f);
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
						default: m !== f && Md(e, t, p, m, r, f);
					}
				}
				Gt(e, s, c, l, u, d, o, a);
				return;
			case "select":
				for (o in m = s = c = p = null, n) if (l = n[o], n.hasOwnProperty(o) && l != null) switch (o) {
					case "value": break;
					case "multiple": m = l;
					default: r.hasOwnProperty(o) || Md(e, t, o, null, r, l);
				}
				for (a in r) if (o = r[a], l = n[a], r.hasOwnProperty(a) && (o != null || l != null)) switch (a) {
					case "value":
						p = o;
						break;
					case "defaultValue":
						c = o;
						break;
					case "multiple": s = o;
					default: o !== l && Md(e, t, a, o, r, l);
				}
				t = c, n = s, r = m, p == null ? !!r != !!n && (t == null ? N(e, !!n, n ? [] : "", !1) : N(e, !!n, t, !0)) : N(e, !!n, p, !1);
				return;
			case "textarea":
				for (c in m = p = null, n) if (a = n[c], n.hasOwnProperty(c) && a != null && !r.hasOwnProperty(c)) switch (c) {
					case "value": break;
					case "children": break;
					default: Md(e, t, c, null, r, a);
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
					default: a !== o && Md(e, t, s, a, r, o);
				}
				Jt(e, p, m);
				return;
			case "option":
				for (var h in n) if (p = n[h], n.hasOwnProperty(h) && p != null && !r.hasOwnProperty(h)) switch (h) {
					case "selected":
						e.selected = !1;
						break;
					default: Md(e, t, h, null, r, p);
				}
				for (l in r) if (p = r[l], m = n[l], r.hasOwnProperty(l) && p !== m && (p != null || m != null)) switch (l) {
					case "selected":
						e.selected = p && typeof p != "function" && typeof p != "symbol";
						break;
					default: Md(e, t, l, p, r, m);
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
				for (var g in n) p = n[g], n.hasOwnProperty(g) && p != null && !r.hasOwnProperty(g) && Md(e, t, g, null, r, p);
				for (u in r) if (p = r[u], m = n[u], r.hasOwnProperty(u) && p !== m && (p != null || m != null)) switch (u) {
					case "children":
					case "dangerouslySetInnerHTML":
						if (p != null) throw Error(i(137, t));
						break;
					default: Md(e, t, u, p, r, m);
				}
				return;
			default: if (en(t)) {
				for (var _ in n) p = n[_], n.hasOwnProperty(_) && p !== void 0 && !r.hasOwnProperty(_) && Nd(e, t, _, void 0, r, p);
				for (d in r) p = r[d], m = n[d], !r.hasOwnProperty(d) || p === m || p === void 0 && m === void 0 || Nd(e, t, d, p, r, m);
				return;
			}
		}
		for (var v in n) p = n[v], n.hasOwnProperty(v) && p != null && !r.hasOwnProperty(v) && Md(e, t, v, null, r, p);
		for (f in r) p = r[f], m = n[f], !r.hasOwnProperty(f) || p === m || p == null && m == null || Md(e, t, f, p, r, m);
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
						a[yt] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && a.rel.toLowerCase() === "stylesheet" || n.removeChild(a), a = o;
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
					ef(n), bt(n);
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
			} else if (!e[yt]) switch (t) {
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
		bt(e);
	}
	var mf = /* @__PURE__ */ new Map(), hf = /* @__PURE__ */ new Set();
	function gf(e) {
		return typeof e.getRootNode == "function" ? e.getRootNode() : e.nodeType === 9 ? e : e.ownerDocument;
	}
	var _f = j.d;
	j.d = {
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
		var e = _f.f(), t = yu();
		return e || t;
	}
	function yf(e) {
		var t = St(e);
		t !== null && t.tag === 5 && t.type === "form" ? Ss(t) : _f.r(e);
	}
	var bf = typeof document > "u" ? null : document;
	function xf(e, t, n) {
		var r = bf;
		if (r && typeof t == "string" && t) {
			var i = Wt(t);
			i = "link[rel=\"" + e + "\"][href=\"" + i + "\"]", typeof n == "string" && (i += "[crossorigin=\"" + n + "\"]"), hf.has(i) || (hf.add(i), e = {
				rel: e,
				crossOrigin: n,
				href: t
			}, r.querySelector(i) === null && (t = r.createElement("link"), Pd(t, "link", e), Tt(t), r.head.appendChild(t)));
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
			var i = "link[rel=\"preload\"][as=\"" + Wt(t) + "\"]";
			t === "image" && n && n.imageSrcSet ? (i += "[imagesrcset=\"" + Wt(n.imageSrcSet) + "\"]", typeof n.imageSizes == "string" && (i += "[imagesizes=\"" + Wt(n.imageSizes) + "\"]")) : i += "[href=\"" + Wt(e) + "\"]";
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
			}, n), mf.set(a, e), r.querySelector(i) !== null || t === "style" && r.querySelector(jf(a)) || t === "script" && r.querySelector(Ff(a)) || (t = r.createElement("link"), Pd(t, "link", e), Tt(t), r.head.appendChild(t)));
		}
	}
	function Tf(e, t) {
		_f.m(e, t);
		var n = bf;
		if (n && e) {
			var r = t && typeof t.as == "string" ? t.as : "script", i = "link[rel=\"modulepreload\"][as=\"" + Wt(r) + "\"][href=\"" + Wt(e) + "\"]", a = i;
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
				r = n.createElement("link"), Pd(r, "link", e), Tt(r), n.head.appendChild(r);
			}
		}
	}
	function Ef(e, t, n) {
		_f.S(e, t, n);
		var r = bf;
		if (r && e) {
			var i = wt(r).hoistableStyles, a = Af(e);
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
					Tt(c), Pd(c, "link", e), c._p = new Promise(function(e, t) {
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
			var r = wt(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), Tt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
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
			var r = wt(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0,
				type: "module"
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), Tt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function kf(e, t, n, r) {
		var a = (a = pe.current) ? gf(a) : null;
		if (!a) throw Error(i(446));
		switch (e) {
			case "meta":
			case "title": return null;
			case "style": return typeof n.precedence == "string" && typeof n.href == "string" ? (t = Af(n.href), n = wt(a).hoistableStyles, r = n.get(t), r || (r = {
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
					var o = wt(a).hoistableStyles, s = o.get(e);
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
			case "script": return t = n.async, n = n.src, typeof n == "string" && t && typeof t != "function" && typeof t != "symbol" ? (t = Pf(n), n = wt(a).hoistableScripts, r = n.get(t), r || (r = {
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
		return "href=\"" + Wt(e) + "\"";
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
		}), Pd(t, "link", n), Tt(t), e.head.appendChild(t));
	}
	function Pf(e) {
		return "[src=\"" + Wt(e) + "\"]";
	}
	function Ff(e) {
		return "script[async]" + e;
	}
	function If(e, t, n) {
		if (t.count++, t.instance === null) switch (t.type) {
			case "style":
				var r = e.querySelector("style[data-href~=\"" + Wt(n.href) + "\"]");
				if (r) return t.instance = r, Tt(r), r;
				var a = h({}, n, {
					"data-href": n.href,
					"data-precedence": n.precedence,
					href: null,
					precedence: null
				});
				return r = (e.ownerDocument || e).createElement("style"), Tt(r), Pd(r, "style", a), Lf(r, n.precedence, e), t.instance = r;
			case "stylesheet":
				a = Af(n.href);
				var o = e.querySelector(jf(a));
				if (o) return t.state.loading |= 4, t.instance = o, Tt(o), o;
				r = Mf(n), (a = mf.get(a)) && Rf(r, a), o = (e.ownerDocument || e).createElement("link"), Tt(o);
				var s = o;
				return s._p = new Promise(function(e, t) {
					s.onload = e, s.onerror = t;
				}), Pd(o, "link", r), t.state.loading |= 4, Lf(o, n.precedence, e), t.instance = o;
			case "script": return o = Pf(n.src), (a = e.querySelector(Ff(o))) ? (t.instance = a, Tt(a), a) : (r = n, (a = mf.get(o)) && (r = h({}, n), zf(r, a)), e = e.ownerDocument || e, a = e.createElement("script"), Tt(a), Pd(a, "link", r), e.head.appendChild(a), t.instance = a);
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
			if (!(a[yt] || a[ft] || e === "link" && a.getAttribute("rel") === "stylesheet") && a.namespaceURI !== "http://www.w3.org/2000/svg") {
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
					t = a._p, typeof t == "object" && t && typeof t.then == "function" && (e.count++, e = Jf.bind(e), t.then(e, e)), n.state.loading |= 4, n.instance = a, Tt(a);
					return;
				}
				a = t.ownerDocument || t, r = Mf(r), (i = mf.get(i)) && Rf(r, i), a = a.createElement("link"), Tt(a);
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
		_currentValue: oe,
		_currentValue2: oe,
		_threadCount: 0
	};
	function $f(e, t, n, r, i, a, o, s, c) {
		this.tag = 1, this.containerInfo = e, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = tt(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = tt(0), this.hiddenUpdates = tt(null), this.identifierPrefix = r, this.onUncaughtError = i, this.onCaughtError = a, this.onRecoverableError = o, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = c, this.incompleteTransitions = /* @__PURE__ */ new Map();
	}
	function ep(e, t, n, r, i, a, o, s, c, l, u, d) {
		return e = new $f(e, t, n, o, c, l, u, d, s), t = 1, !0 === a && (t |= 24), a = ui(3, null, null, t), e.current = a, a.stateNode = e, t = la(), t.refCount++, e.pooledCache = t, t.refCount++, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: t
		}, Va(a), e;
	}
	function tp(e) {
		return e ? (e = ci, e) : ci;
	}
	function np(e, t, n, r, i, a) {
		i = tp(i), r.context === null ? r.context = i : r.pendingContext = i, r = B(t), r.payload = { element: n }, a = a === void 0 ? null : a, a !== null && (r.callback = a), n = Ua(e, r, t), n !== null && (mu(n, e, t), Wa(n, e, t));
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
			t !== null && mu(t, e, 67108864), ip(e, 67108864);
		}
	}
	function op(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = fu();
			t = st(t);
			var n = ai(e, t);
			n !== null && mu(n, e, t), ip(e, t);
		}
	}
	var sp = !0;
	function cp(e, t, n, r) {
		var i = A.T;
		A.T = null;
		var a = j.p;
		try {
			j.p = 2, up(e, t, n, r);
		} finally {
			j.p = a, A.T = i;
		}
	}
	function lp(e, t, n, r) {
		var i = A.T;
		A.T = null;
		var a = j.p;
		try {
			j.p = 8, up(e, t, n, r);
		} finally {
			j.p = a, A.T = i;
		}
	}
	function up(e, t, n, r) {
		if (sp) {
			var i = dp(r);
			if (i === null) Cd(e, t, r, fp, n), Cp(e, r);
			else if (Tp(i, e, t, n, r)) r.stopPropagation();
			else if (Cp(e, r), t & 4 && -1 < Sp.indexOf(e)) {
				for (; i !== null;) {
					var a = St(i);
					if (a !== null) switch (a.tag) {
						case 3:
							if (a = a.stateNode, a.current.memoizedState.isDehydrated) {
								var o = Xe(a.pendingLanes);
								if (o !== 0) {
									var s = a;
									for (s.pendingLanes |= 2, s.entangledLanes |= 2; o;) {
										var c = 1 << 31 - Ue(o);
										s.entanglements[1] |= c, o &= ~c;
									}
									nd(a), !(J & 6) && (eu = je() + 500, rd(0, !1));
								}
							}
							break;
						case 31:
						case 13: s = ai(a, 2), s !== null && mu(s, a, 2), yu(), ip(a, 2);
					}
					if (a = dp(r), a === null && Cd(e, t, r, fp, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else Cd(e, t, r, null, n);
		}
	}
	function dp(e) {
		return e = sn(e), pp(e);
	}
	var fp = null;
	function pp(e) {
		if (fp = null, e = xt(e), e !== null) {
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
			case "message": switch (Me()) {
				case Ne: return 2;
				case Pe: return 8;
				case Fe:
				case Ie: return 32;
				case Le: return 268435456;
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
		}, t !== null && (t = St(t), t !== null && ap(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
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
		var t = xt(e.target);
		if (t !== null) {
			var n = o(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = s(n), t !== null) {
						e.blockedOn = t, ut(e.priority, function() {
							op(n);
						});
						return;
					}
				} else if (t === 31) {
					if (t = c(n), t !== null) {
						e.blockedOn = t, ut(e.priority, function() {
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
			} else return t = St(n), t !== null && ap(t), e.blockedOn = n, !1;
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
				var a = St(n);
				a !== null && (e.splice(t, 3), t -= 3, bs(a, {
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
			var i = n[r], a = n[r + 1], o = i[pt] || null;
			if (typeof a == "function") o || Mp(n);
			else if (o) {
				var s = null;
				if (a && a.hasAttribute("formAction")) {
					if (i = a, o = a[pt] || null) s = o.formAction;
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
		np(n, fu(), e, t, null, null);
	}, Ip.prototype.unmount = Fp.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			np(e.current, 2, null, e, null, null), yu(), t[mt] = null;
		}
	};
	function Ip(e) {
		this._internalRoot = e;
	}
	Ip.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = lt();
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
	j.findDOMNode = function(e) {
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(i(188)) : (e = Object.keys(e).join(","), Error(i(268, e)));
		return e = d(t), e = e === null ? null : p(e), e = e === null ? null : e.stateNode, e;
	};
	var Rp = {
		bundleType: 0,
		version: "19.2.8",
		rendererPackageName: "react-dom",
		currentDispatcherRef: A,
		reconcilerVersion: "19.2.8"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var zp = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!zp.isDisabled && zp.supportsFiber) try {
			Be = zp.inject(Rp), Ve = zp;
		} catch {}
	}
	e.createRoot = function(e, t) {
		if (!a(e)) throw Error(i(299));
		var n = !1, r = "", o = Us, s = Ws, c = Gs;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (r = t.identifierPrefix), t.onUncaughtError !== void 0 && (o = t.onUncaughtError), t.onCaughtError !== void 0 && (s = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError)), t = ep(e, 1, !1, null, null, n, r, null, o, s, c, Pp), e[mt] = t.current, xd(e), new Fp(t);
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
function T() {
	return y?.userAccess ?? null;
}
//#endregion
//#region src/lib/dispatcher.ts
var ee = /* @__PURE__ */ new Set(/* @__PURE__ */ "shipment_update.navigate.shipment_field_save.delivery_confirm.finance_actual_save.payment_record.payment_correction.partner_payable_record.partner_payment_record.shipment_create.pxk_generate.customer_create.customer_edit.customer_archive.customer_import.quote_create.quote_edit.quote_transition.agreement_create.agreement_edit.agreement_transition.contract_create.contract_save.contract_goods_save.contract_docgen_generate.contract_docgen_issue.contract_shipment_link.tariff_lookup.translate_text.partner_context_select.reconciliation_filter".split(".")), E = null, D = 0;
function O(e) {
	E = e;
}
function te(e, t) {
	return !E || !ee.has(e) ? !1 : (D += 1, E(e, {
		seq: D,
		event: e,
		payload: t
	}), !0);
}
//#endregion
//#region node_modules/react-router/dist/development/chunk-BV7QT456.mjs
var k = /^(?:[a-z][a-z0-9+.-]*:|[\\/]{2})/i, ne = /^[\\/]{2}/;
function re(e, t) {
	return t + e.replace(/\\/g, "/");
}
function ie(e) {
	return typeof e == "object" && !!e && "pathname" in e && "search" in e && "hash" in e && "state" in e && "key" in e;
}
function ae(e = {}) {
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
		let a = se(i ? l().pathname : "/", e, t, n, r);
		return j(a.pathname.charAt(0) === "/", `relative pathnames are not supported in memory history: ${JSON.stringify(e)}`), a;
	}
	function d(e) {
		return typeof e == "string" ? e : ce(e);
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
			let t = typeof e == "string" ? le(e) : e;
			return {
				pathname: t.pathname || "",
				search: t.search || "",
				hash: t.hash || ""
			};
		},
		push(e, t) {
			o = "PUSH";
			let n = ie(e) ? e : u(e, t);
			a += 1, i.splice(a, i.length, n), r && s && s({
				action: o,
				location: n,
				delta: 1
			});
		},
		replace(e, t) {
			o = "REPLACE";
			let n = ie(e) ? e : u(e, t);
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
function oe() {
	return Math.random().toString(36).substring(2, 10);
}
function se(e, t, n = null, r, i) {
	return {
		pathname: typeof e == "string" ? e : e.pathname,
		search: "",
		hash: "",
		...typeof t == "string" ? le(t) : t,
		state: n,
		key: t && t.key || r || oe(),
		mask: i
	};
}
function ce({ pathname: e = "/", search: t = "", hash: n = "" }) {
	return t && t !== "?" && (e += t.charAt(0) === "?" ? t : "?" + t), n && n !== "#" && (e += n.charAt(0) === "#" ? n : "#" + n), e;
}
function le(e) {
	let t = {};
	if (e) {
		let n = e.indexOf("#");
		n >= 0 && (t.hash = e.substring(n), e = e.substring(0, n));
		let r = e.indexOf("?");
		r >= 0 && (t.search = e.substring(r), e = e.substring(0, r)), e && (t.pathname = e);
	}
	return t;
}
function ue(e, t, n = "/") {
	return M(e, t, n, !1);
}
function M(e, t, n, r, i) {
	let a = ke((typeof t == "string" ? le(t) : t).pathname || "/", n);
	if (a == null) return null;
	let o = i ?? de(e), s = null, c = Oe(a);
	for (let e = 0; s == null && e < o.length; ++e) s = we(o[e], c, r);
	return s;
}
function de(e) {
	let t = fe(e);
	return me(t), t;
}
function fe(e, t = [], n = [], r = "", i = !1) {
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
		let l = Le([r, c.relativePath]), u = n.concat(c);
		e.children && e.children.length > 0 && (A(e.index !== !0, `Index routes must not have child routes. Please remove all child routes from route path "${l}".`), fe(e.children, t, u, l, o)), (e.path != null || e.index) && t.push({
			path: l,
			score: Se(l, e.index),
			routesMeta: u.map((e, t) => {
				let [n, r] = De(e.relativePath, e.caseSensitive, t === u.length - 1);
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
		else for (let n of pe(e.path)) a(e, t, !0, n);
	}), t;
}
function pe(e) {
	let t = e.split("/");
	if (t.length === 0) return [];
	let [n, ...r] = t, i = n.endsWith("?"), a = n.replace(/\?$/, "");
	if (r.length === 0) return i ? [a, ""] : [a];
	let o = pe(r.join("/")), s = [];
	return s.push(...o.map((e) => e === "" ? a : [a, e].join("/"))), i && s.push(...o), s.map((t) => e.startsWith("/") && t === "" ? "/" : t);
}
function me(e) {
	e.sort((e, t) => e.score === t.score ? Ce(e.routesMeta.map((e) => e.childrenIndex), t.routesMeta.map((e) => e.childrenIndex)) : t.score - e.score);
}
var he = /^:[\w-]+$/, ge = 3, _e = 2, ve = 1, ye = 10, be = -2, xe = (e) => e === "*";
function Se(e, t) {
	let n = e.split("/"), r = n.length;
	return n.some(xe) && (r += be), t && (r += _e), n.filter((e) => !xe(e)).reduce((e, t) => e + (he.test(t) ? ge : t === "" ? ve : ye), r);
}
function Ce(e, t) {
	return e.length === t.length && e.slice(0, -1).every((e, n) => e === t[n]) ? e[e.length - 1] - t[t.length - 1] : 0;
}
function we(e, t, n = !1) {
	let { routesMeta: r } = e, i = {}, a = "/", o = [];
	for (let e = 0; e < r.length; ++e) {
		let s = r[e], c = e === r.length - 1, l = a === "/" ? t : t.slice(a.length) || "/", u = {
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: c
		}, d = s.matcher && s.compiledParams ? Ee(u, l, s.matcher, s.compiledParams) : Te(u, l), f = s.route;
		if (!d && c && n && !r[r.length - 1].route.index && (d = Te({
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: !1
		}, l)), !d) return null;
		Object.assign(i, d.params), o.push({
			params: i,
			pathname: Le([a, d.pathname]),
			pathnameBase: ze(Le([a, d.pathnameBase])),
			route: f
		}), d.pathnameBase !== "/" && (a = Le([a, d.pathnameBase]));
	}
	return o;
}
function Te(e, t) {
	typeof e == "string" && (e = {
		path: e,
		caseSensitive: !1,
		end: !0
	});
	let [n, r] = De(e.path, e.caseSensitive, e.end);
	return Ee(e, t, n, r);
}
function Ee(e, t, n, r) {
	let i = t.match(n);
	if (!i) return null;
	let a = i[0], o = Re(a, 1), s = i.slice(1);
	return {
		params: r.reduce((e, { paramName: t, isOptional: n }, r) => {
			if (t === "*") {
				let e = s[r] || "";
				o = Re(a.slice(0, a.length - e.length), 1);
			}
			let i = s[r];
			return e[t] = n && !i ? void 0 : (i || "").replace(/%2F/g, "/"), e;
		}, {}),
		pathname: a,
		pathnameBase: o,
		pattern: e
	};
}
function De(e, t = !1, n = !0) {
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
function Oe(e) {
	try {
		return e.split("/").map((e) => decodeURIComponent(e).replace(/\//g, "%2F")).join("/");
	} catch (t) {
		return j(!1, `The URL path "${e}" could not be decoded because it is a malformed URL segment. This is probably due to a bad percent encoding (${t}).`), e;
	}
}
function ke(e, t) {
	if (t === "/") return e;
	if (!e.toLowerCase().startsWith(t.toLowerCase())) return null;
	let n = t.endsWith("/") ? t.length - 1 : t.length, r = e.charAt(n);
	return r && r !== "/" ? null : e.slice(n) || "/";
}
function Ae(e, t = "/") {
	let { pathname: n, search: r = "", hash: i = "" } = typeof e == "string" ? le(e) : e, a;
	return n ? (n = Ie(n), a = n.startsWith("/") || n.startsWith("\\") ? je(n.substring(1), "/") : je(n, t)) : a = t, {
		pathname: a,
		search: Be(r),
		hash: Ve(i)
	};
}
function je(e, t) {
	let n = Re(t).split("/");
	return e.split("/").forEach((e) => {
		e === ".." ? n.length > 1 && n.pop() : e !== "." && n.push(e);
	}), n.length > 1 ? n.join("/") : "/";
}
function Me(e, t, n, r) {
	return `Cannot include a '${e}' character in a manually specified \`to.${t}\` field [${JSON.stringify(r)}].  Please separate it out to the \`to.${n}\` field. Alternatively you may provide the full path as a string in <Link to="..."> and the router will parse it for you.`;
}
function Ne(e) {
	return e.filter((e, t) => t === 0 || e.route.path && e.route.path.length > 0);
}
function Pe(e) {
	let t = Ne(e);
	return t.map((e, n) => n === t.length - 1 ? e.pathname : e.pathnameBase);
}
function Fe(e, t, n, r = !1) {
	let i;
	typeof e == "string" ? i = le(e) : (i = { ...e }, A(!i.pathname || !i.pathname.includes("?"), Me("?", "pathname", "search", i)), A(!i.pathname || !i.pathname.includes("#"), Me("#", "pathname", "hash", i)), A(!i.search || !i.search.includes("#"), Me("#", "search", "hash", i)));
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
	let c = Ae(i, s), l = o && o !== "/" && o.endsWith("/"), u = (a || o === ".") && n.endsWith("/");
	return !c.pathname.endsWith("/") && (l || u) && (c.pathname += "/"), c;
}
var Ie = (e) => e.replace(/[\\/]{2,}/g, "/"), Le = (e) => Ie(e.join("/"));
function Re(e, t = 0) {
	let n = e.length;
	for (; n > t && e.charCodeAt(n - 1) === 47;) n--;
	return n === e.length ? e : e.slice(0, n);
}
var ze = (e) => Re(e).replace(/^\/*/, "/"), Be = (e) => !e || e === "?" ? "" : e.startsWith("?") ? e : "?" + e, Ve = (e) => !e || e === "#" ? "" : e.startsWith("#") ? e : "#" + e, He = class {
	constructor(e, t, n, r = !1) {
		this.status = e, this.statusText = t || "", this.internal = r, n instanceof Error ? (this.data = n.toString(), this.error = n) : this.data = n;
	}
};
function Ue(e) {
	return e != null && typeof e.status == "number" && typeof e.statusText == "string" && typeof e.internal == "boolean" && "data" in e;
}
function We(e) {
	return Le(e.map((e) => e.route.path).filter(Boolean)) || "/";
}
var Ge = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
function Ke(e, t) {
	let n = e;
	if (typeof n != "string" || !k.test(n)) return {
		absoluteURL: void 0,
		isExternal: !1,
		to: n
	};
	let r = n, i = !1;
	if (Ge) try {
		let e = new URL(window.location.href), r = ne.test(n) ? new URL(re(n, e.protocol)) : new URL(n), a = ke(r.pathname, t);
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
var qe = new URL("http://localhost");
function Je(e) {
	if (e.createURL) return e.createURL("/");
	try {
		return new URL(e.createHref("/"), qe);
	} catch {
		return qe;
	}
}
function Ye(e, t) {
	return e.origin === t.origin && (e.origin !== "null" || e.protocol === t.protocol && e.host === t.host);
}
function Xe(e, t) {
	if (e.startsWith("//")) return !0;
	let n = t.protocol.toLowerCase();
	return e.toLowerCase().startsWith(n) ? t.host === "" || e.slice(n.length).startsWith("//") : !1;
}
function Ze(e, t, n, r) {
	let i = null;
	try {
		i = e == null ? null : new URL(e, n);
	} catch {}
	let a = new URL(t, n), o = i != null && !Ye(i, n), s = !Ye(a, n);
	if (r === "reject") {
		if (o || s) throw Error("External navigation is not allowed");
	} else if (s && (i == null || !Xe(e, i) || !Ye(i, a))) throw Error("External navigation is not allowed");
}
var Qe = [
	"POST",
	"PUT",
	"PATCH",
	"DELETE"
];
new Set(Qe);
var $e = ["GET", ...Qe];
new Set($e);
var et = [
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
function tt(e) {
	try {
		return et.includes(new URL(e).protocol);
	} catch {
		return !1;
	}
}
var nt = _.createContext(null);
nt.displayName = "DataRouter";
var rt = _.createContext(null);
rt.displayName = "DataRouterState";
var it = _.createContext(!1);
function at() {
	return _.useContext(it);
}
var ot = _.createContext({ isTransitioning: !1 });
ot.displayName = "ViewTransition";
var st = _.createContext(/* @__PURE__ */ new Map());
st.displayName = "Fetchers";
var ct = _.createContext(null);
ct.displayName = "Await";
var lt = _.createContext(null);
lt.displayName = "Navigation";
var ut = _.createContext(null);
ut.displayName = "Location";
var dt = _.createContext({
	outlet: null,
	matches: [],
	isDataRoute: !1
});
dt.displayName = "Route";
var ft = _.createContext(null);
ft.displayName = "RouteError";
var pt = "REACT_ROUTER_ERROR", mt = "REDIRECT", ht = "ROUTE_ERROR_RESPONSE";
function gt(e) {
	if (e.startsWith(`${pt}:${mt}:{`)) try {
		let t = JSON.parse(e.slice(28));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string" && typeof t.location == "string" && typeof t.reloadDocument == "boolean" && typeof t.replace == "boolean") return t;
	} catch {}
}
function _t(e) {
	if (e.startsWith(`${pt}:${ht}:{`)) try {
		let t = JSON.parse(e.slice(40));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string") return new He(t.status, t.statusText, t.data);
	} catch {}
}
function vt(e, { relative: t } = {}) {
	A(yt(), "useHref() may be used only in the context of a <Router> component.");
	let { basename: n, navigator: r } = _.useContext(lt), { hash: i, pathname: a, search: o } = Et(e, { relative: t }), s = a;
	return n !== "/" && (s = a === "/" ? n : Le([n, a])), r.createHref({
		pathname: s,
		search: o,
		hash: i
	});
}
function yt() {
	return _.useContext(ut) != null;
}
function bt() {
	return A(yt(), "useLocation() may be used only in the context of a <Router> component."), _.useContext(ut).location;
}
var xt = "You should call navigate() in a React.useEffect(), not when your component is first rendered.";
function St(e) {
	_.useContext(lt).static || _.useLayoutEffect(e);
}
function Ct() {
	let { isDataRoute: e } = _.useContext(dt);
	return e ? Ut() : wt();
}
function wt() {
	A(yt(), "useNavigate() may be used only in the context of a <Router> component.");
	let e = _.useContext(nt), { basename: t, navigator: n } = _.useContext(lt), { matches: r } = _.useContext(dt), { pathname: i } = bt(), a = JSON.stringify(Pe(r)), o = _.useRef(!1);
	return St(() => {
		o.current = !0;
	}), _.useCallback((r, s = {}) => {
		if (j(o.current, xt), !o.current) return;
		if (typeof r == "number") {
			n.go(r);
			return;
		}
		let c = Fe(r, JSON.parse(a), i, s.relative === "path");
		e == null && t !== "/" && (c.pathname = c.pathname === "/" ? t : Le([t, c.pathname])), Ze(typeof r == "string" ? r : ce(r), n.createHref(c), Je(n), "reject"), (s.replace ? n.replace : n.push)(c, s.state, s);
	}, [
		t,
		n,
		a,
		i,
		e
	]);
}
_.createContext(null);
function Tt() {
	let { matches: e } = _.useContext(dt);
	return e[e.length - 1]?.params ?? {};
}
function Et(e, { relative: t } = {}) {
	let { matches: n } = _.useContext(dt), { pathname: r } = bt(), i = JSON.stringify(Pe(n));
	return _.useMemo(() => Fe(e, JSON.parse(i), r, t === "path"), [
		e,
		i,
		r,
		t
	]);
}
function Dt(e, t) {
	return Ot(e, t);
}
function Ot(e, t, n) {
	A(yt(), "useRoutes() may be used only in the context of a <Router> component.");
	let { navigator: r } = _.useContext(lt), { matches: i } = _.useContext(dt), a = i[i.length - 1], o = a ? a.params : {}, s = a ? a.pathname : "/", c = a ? a.pathnameBase : "/", l = a && a.route;
	{
		let e = l && l.path || "";
		Gt(s, !l || e.endsWith("*") || e.endsWith("*?"), `You rendered descendant <Routes> (or called \`useRoutes()\`) at "${s}" (under <Route path="${e}">) but the parent route path has no trailing "*". This means if you navigate deeper, the parent won't match anymore and therefore the child routes will never render.

Please change the parent <Route path="${e}"> to <Route path="${e === "/" ? "*" : `${e}/*`}">.`);
	}
	let u = bt(), d;
	if (t) {
		let e = typeof t == "string" ? le(t) : t;
		A(c === "/" || e.pathname?.startsWith(c), `When overriding the location using \`<Routes location>\` or \`useRoutes(routes, location)\`, the location pathname must begin with the portion of the URL pathname that was matched by all parent routes. The current pathname base is "${c}" but pathname "${e.pathname}" was given in the \`location\` prop.`), d = e;
	} else d = u;
	let f = d.pathname || "/", p = f;
	if (c !== "/") {
		let e = c.replace(/^\//, "").split("/");
		p = "/" + f.replace(/^\//, "").split("/").slice(e.length).join("/");
	}
	let m = n && n.state.matches.length ? n.state.matches.map((e) => Object.assign(e, { route: n.manifest[e.route.id] || e.route })) : ue(e, { pathname: p });
	j(l || m != null, `No routes matched location "${d.pathname}${d.search}${d.hash}" `), j(m == null || m[m.length - 1].route.element !== void 0 || m[m.length - 1].route.Component !== void 0 || m[m.length - 1].route.lazy !== void 0, `Matched leaf route at location "${d.pathname}${d.search}${d.hash}" does not have an element or Component. This means it will render an <Outlet /> with a null value by default resulting in an "empty" page.`);
	let h = Ft(m && m.map((e) => Object.assign({}, e, {
		params: Object.assign({}, o, e.params),
		pathname: Le([c, r.encodeLocation ? r.encodeLocation(e.pathname.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathname]),
		pathnameBase: e.pathnameBase === "/" ? c : Le([c, r.encodeLocation ? r.encodeLocation(e.pathnameBase.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathnameBase])
	})), i, n);
	return t && h ? /* @__PURE__ */ _.createElement(ut.Provider, { value: {
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
function kt() {
	let e = Ht(), t = Ue(e) ? `${e.status} ${e.statusText}` : e instanceof Error ? e.message : JSON.stringify(e), n = e instanceof Error ? e.stack : null, r = "rgba(200,200,200, 0.5)", i = {
		padding: "0.5rem",
		backgroundColor: r
	}, a = {
		padding: "2px 4px",
		backgroundColor: r
	}, o = null;
	return console.error("Error handled by React Router default ErrorBoundary:", e), o = /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("p", null, "💿 Hey developer 👋"), /* @__PURE__ */ _.createElement("p", null, "You can provide a way better UX than this when your app throws errors by providing your own ", /* @__PURE__ */ _.createElement("code", { style: a }, "ErrorBoundary"), " or", " ", /* @__PURE__ */ _.createElement("code", { style: a }, "errorElement"), " prop on your route.")), /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("h2", null, "Unexpected Application Error!"), /* @__PURE__ */ _.createElement("h3", { style: { fontStyle: "italic" } }, t), n ? /* @__PURE__ */ _.createElement("pre", { style: i }, n) : null, o);
}
var At = /* @__PURE__ */ _.createElement(kt, null), jt = class extends _.Component {
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
			let t = _t(e.digest);
			t && (e = t);
		}
		let t = e === void 0 ? this.props.children : /* @__PURE__ */ _.createElement(dt.Provider, { value: this.props.routeContext }, /* @__PURE__ */ _.createElement(ft.Provider, {
			value: e,
			children: this.props.component
		}));
		return this.context ? /* @__PURE__ */ _.createElement(Nt, { error: e }, t) : t;
	}
};
jt.contextType = it;
var Mt = /* @__PURE__ */ new WeakMap();
function Nt({ children: e, error: t }) {
	let { basename: n, navigator: r } = _.useContext(lt);
	if (typeof t == "object" && t && "digest" in t && typeof t.digest == "string") {
		let e = gt(t.digest);
		if (e) {
			let i = Mt.get(t);
			if (i) throw i;
			let a = Ke(e.location, n), o = a.absoluteURL || a.to;
			if (Ze(e.location, o, Je(r), "allow-explicit"), tt(o)) throw Error("Invalid redirect location");
			if (Ge && !Mt.get(t)) {
				if (a.isExternal || e.reloadDocument) window.location.href = o;
				else {
					let n = Promise.resolve().then(() => window.__reactRouterDataRouter.navigate(a.to, { replace: e.replace }));
					throw Mt.set(t, n), n;
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
function Pt({ routeContext: e, match: t, children: n }) {
	let r = _.useContext(nt);
	return r && r.static && r.staticContext && (t.route.errorElement || t.route.ErrorBoundary) && (r.staticContext._deepestRenderedBoundaryId = t.route.id), /* @__PURE__ */ _.createElement(dt.Provider, { value: e }, n);
}
function Ft(e, t = [], n) {
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
			pattern: We(r.matches),
			errorInfo: t
		});
	} : void 0;
	return i.reduceRight((e, n, c) => {
		let u, d = !1, f = null, p = null;
		r && (u = a && n.route.id ? a[n.route.id] : void 0, f = n.route.errorElement || At, o && (s < 0 && c === 0 ? (Gt("route-fallback", !1, "No `HydrateFallback` element provided to render during initial hydration"), d = !0, p = null) : s === c && (d = !0, p = n.route.hydrateFallbackElement || null)));
		let m = t.concat(i.slice(0, c + 1)), h = () => {
			let t;
			return t = u ? f : d ? p : n.route.Component ? /* @__PURE__ */ _.createElement(n.route.Component, null) : n.route.element ? n.route.element : e, /* @__PURE__ */ _.createElement(Pt, {
				match: n,
				routeContext: {
					outlet: e,
					matches: m,
					isDataRoute: r != null
				},
				children: t
			});
		};
		return r && (n.route.ErrorBoundary || n.route.errorElement || c === 0) ? /* @__PURE__ */ _.createElement(jt, {
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
function It(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function Lt(e) {
	let t = _.useContext(nt);
	return A(t, It(e)), t;
}
function Rt(e) {
	let t = _.useContext(rt);
	return A(t, It(e)), t;
}
function zt(e) {
	let t = _.useContext(dt);
	return A(t, It(e)), t;
}
function Bt(e) {
	let t = zt(e), n = t.matches[t.matches.length - 1];
	return A(n.route.id, `${e} can only be used on routes that contain a unique "id"`), n.route.id;
}
function Vt() {
	return Bt("useRouteId");
}
function Ht() {
	let e = _.useContext(ft), t = Rt("useRouteError"), n = Bt("useRouteError");
	return e === void 0 ? t.errors?.[n] : e;
}
function Ut() {
	let { router: e } = Lt("useNavigate"), t = Bt("useNavigate"), n = _.useRef(!1);
	return St(() => {
		n.current = !0;
	}), _.useCallback(async (r, i = {}) => {
		j(n.current, xt), n.current && (typeof r == "number" ? await e.navigate(r) : await e.navigate(r, {
			fromRouteId: t,
			...i
		}));
	}, [e, t]);
}
var Wt = {};
function Gt(e, t, n) {
	!t && !Wt[e] && (Wt[e] = !0, j(!1, n));
}
_.memo(Kt);
function Kt({ routes: e, manifest: t, future: n, state: r, isStatic: i, onError: a }) {
	return Ot(e, void 0, {
		manifest: t,
		state: r,
		isStatic: i,
		onError: a,
		future: n
	});
}
function qt({ basename: e, children: t, initialEntries: n, initialIndex: r, useTransitions: i }) {
	let a = _.useRef();
	a.current ?? (a.current = ae({
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
	return _.useLayoutEffect(() => o.listen(l), [o, l]), /* @__PURE__ */ _.createElement(Jt, {
		basename: e,
		children: t,
		location: s.location,
		navigationType: s.action,
		navigator: o,
		useTransitions: i
	});
}
function N(e) {
	A(!1, "A <Route> is only ever to be used as the child of <Routes> element, never rendered directly. Please wrap your <Route> in a <Routes>.");
}
function Jt({ basename: e = "/", children: t = null, location: n, navigationType: r = "POP", navigator: i, static: a = !1, useTransitions: o }) {
	A(!yt(), "You cannot render a <Router> inside another <Router>. You should never have more than one in your app.");
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
	typeof n == "string" && (n = le(n));
	let { pathname: l = "/", search: u = "", hash: d = "", state: f = null, key: p = "default", mask: m } = n, h = _.useMemo(() => {
		let e = ke(l, s);
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
	return j(h != null, `<Router basename="${s}"> is not able to match the URL "${l}${u}${d}" because it does not start with the basename, so the <Router> won't render anything.`), h == null ? null : /* @__PURE__ */ _.createElement(lt.Provider, { value: c }, /* @__PURE__ */ _.createElement(ut.Provider, {
		children: t,
		value: h
	}));
}
function Yt({ children: e, location: t }) {
	return Dt(Xt(e), t);
}
_.Component;
function Xt(e, t = []) {
	let n = [];
	return _.Children.forEach(e, (e, r) => {
		if (!_.isValidElement(e)) return;
		let i = [...t, r];
		if (e.type === _.Fragment) {
			n.push.apply(n, Xt(e.props.children, i));
			return;
		}
		A(e.type === N, `[${typeof e.type == "string" ? e.type : e.type.name}] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>`), A(!e.props.index || !e.props.children, "An index route cannot have child routes.");
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
		e.props.children && (a.children = Xt(e.props.children, i)), n.push(a);
	}), n;
}
var Zt = "get", Qt = "application/x-www-form-urlencoded";
function $t(e) {
	return typeof HTMLElement < "u" && e instanceof HTMLElement;
}
function en(e) {
	return $t(e) && e.tagName.toLowerCase() === "button";
}
function tn(e) {
	return $t(e) && e.tagName.toLowerCase() === "form";
}
function nn(e) {
	return $t(e) && e.tagName.toLowerCase() === "input";
}
function rn(e) {
	return !!(e.metaKey || e.altKey || e.ctrlKey || e.shiftKey);
}
function an(e, t) {
	return e.button === 0 && (!t || t === "_self") && !rn(e);
}
function on(e = "") {
	return new URLSearchParams(typeof e == "string" || Array.isArray(e) || e instanceof URLSearchParams ? e : Object.keys(e).reduce((t, n) => {
		let r = e[n];
		return t.concat(Array.isArray(r) ? r.map((e) => [n, e]) : [[n, r]]);
	}, []));
}
function sn(e, t) {
	let n = on(e);
	return t && t.forEach((e, r) => {
		n.has(r) || t.getAll(r).forEach((e) => {
			n.append(r, e);
		});
	}), n;
}
var cn = null;
function ln() {
	if (cn === null) try {
		new FormData(document.createElement("form"), 0), cn = !1;
	} catch {
		cn = !0;
	}
	return cn;
}
var un = /* @__PURE__ */ new Set([
	"application/x-www-form-urlencoded",
	"multipart/form-data",
	"text/plain"
]);
function dn(e) {
	return e != null && !un.has(e) ? (j(!1, `"${e}" is not a valid \`encType\` for \`<Form>\`/\`<fetcher.Form>\` and will default to "${Qt}"`), null) : e;
}
function fn(e, t) {
	let n, r, i, a, o;
	if (tn(e)) {
		let o = e.getAttribute("action");
		r = o ? ke(o, t) : null, n = e.getAttribute("method") || Zt, i = dn(e.getAttribute("enctype")) || Qt, a = new FormData(e);
	} else if (en(e) || nn(e) && (e.type === "submit" || e.type === "image")) {
		let o = e.form;
		if (o == null) throw Error("Cannot submit a <button> or <input type=\"submit\"> without a <form>");
		let s = e.getAttribute("formaction") || o.getAttribute("action");
		if (r = s ? ke(s, t) : null, n = e.getAttribute("formmethod") || o.getAttribute("method") || Zt, i = dn(e.getAttribute("formenctype")) || dn(o.getAttribute("enctype")) || Qt, a = new FormData(o, e), !ln()) {
			let { name: t, type: n, value: r } = e;
			if (n === "image") {
				let e = t ? `${t}.` : "";
				a.append(`${e}x`, "0"), a.append(`${e}y`, "0");
			} else t && a.append(t, r);
		}
	} else if ($t(e)) throw Error("Cannot submit element that is not <form>, <button>, or <input type=\"submit|image\">");
	else n = Zt, r = null, i = Qt, o = e;
	return a && i === "text/plain" && (o = a, a = void 0), {
		action: r,
		method: n.toLowerCase(),
		encType: i,
		formData: a,
		body: o
	};
}
Object.getOwnPropertyNames(Object.prototype).sort().join("\0");
function pn(e, t) {
	if (e === !1 || e == null) throw Error(t);
}
function mn(e, t, n, r) {
	let i = typeof e == "string" ? new URL(e, typeof window > "u" ? "server://singlefetch/" : window.location.origin) : e;
	return i.pathname = n ? i.pathname.endsWith("/") ? `${i.pathname}_.${r}` : `${i.pathname}.${r}` : i.pathname === "/" ? `_root.${r}` : t && ke(i.pathname, t) === "/" ? `${Re(t)}/_root.${r}` : `${Re(i.pathname)}.${r}`, i;
}
async function hn(e, t) {
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
function gn(e) {
	return e != null && typeof e.page == "string";
}
function _n(e) {
	return e == null ? !1 : e.href == null ? e.rel === "preload" && typeof e.imageSrcSet == "string" && typeof e.imageSizes == "string" : typeof e.rel == "string" && typeof e.href == "string";
}
async function vn(e, t, n) {
	return Cn((await Promise.all(e.map(async (e) => {
		let r = t.routes[e.route.id];
		if (r) {
			let e = await hn(r, n);
			return e.links ? e.links() : [];
		}
		return [];
	}))).flat(1).filter(_n).filter((e) => e.rel === "stylesheet" || e.rel === "preload").map((e) => e.rel === "stylesheet" ? {
		...e,
		rel: "prefetch",
		as: "style"
	} : {
		...e,
		rel: "prefetch"
	}));
}
function yn(e, t, n, r, i, a) {
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
function bn(e, t, { includeHydrateFallback: n } = {}) {
	return xn(e.map((e) => {
		let r = t.routes[e.route.id];
		if (!r) return [];
		let i = [r.module];
		return r.clientActionModule && (i = i.concat(r.clientActionModule)), r.clientLoaderModule && (i = i.concat(r.clientLoaderModule)), n && r.hydrateFallbackModule && (i = i.concat(r.hydrateFallbackModule)), r.imports && (i = i.concat(r.imports)), i;
	}).flat(1));
}
function xn(e) {
	return [...new Set(e)];
}
function Sn(e) {
	let t = {}, n = Object.keys(e).sort();
	for (let r of n) t[r] = e[r];
	return t;
}
function Cn(e, t) {
	let n = /* @__PURE__ */ new Set(), r = new Set(t);
	return e.reduce((e, i) => {
		if (t && !gn(i) && i.as === "script" && i.href && r.has(i.href)) return e;
		let a = JSON.stringify(Sn(i));
		return n.has(a) || (n.add(a), e.push({
			key: a,
			link: i
		})), e;
	}, []);
}
function wn() {
	let e = _.useContext(nt);
	return pn(e, "You must render this element inside a <DataRouterContext.Provider> element"), e;
}
function Tn() {
	let e = _.useContext(rt);
	return pn(e, "You must render this element inside a <DataRouterStateContext.Provider> element"), e;
}
var En = _.createContext(void 0);
En.displayName = "FrameworkContext";
function Dn() {
	let e = _.useContext(En);
	return pn(e, "You must render this element inside a <HydratedRouter> element"), e;
}
function On(e, t) {
	let n = _.useContext(En), [r, i] = _.useState(!1), [a, o] = _.useState(!1), { onFocus: s, onBlur: c, onMouseEnter: l, onMouseLeave: u, onTouchStart: d } = t, f = _.useRef(null);
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
			onFocus: kn(s, p),
			onBlur: kn(c, m),
			onMouseEnter: kn(l, p),
			onMouseLeave: kn(u, m),
			onTouchStart: kn(d, p)
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
function kn(e, t) {
	return (n) => {
		e && e(n), n.defaultPrevented || t(n);
	};
}
function An({ page: e, ...t }) {
	let n = at(), { nonce: r } = Dn(), { router: i } = wn(), a = _.useMemo(() => ue(i.routes, e, i.basename), [
		i.routes,
		e,
		i.basename
	]);
	return a ? (t.nonce == null && r && (t = {
		...t,
		nonce: r
	}), n ? /* @__PURE__ */ _.createElement(Mn, {
		page: e,
		matches: a,
		...t
	}) : /* @__PURE__ */ _.createElement(Nn, {
		page: e,
		matches: a,
		...t
	})) : null;
}
function jn(e) {
	let { manifest: t, routeModules: n } = Dn(), [r, i] = _.useState([]);
	return _.useEffect(() => {
		let r = !1;
		return vn(e, t, n).then((e) => {
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
function Mn({ page: e, matches: t, ...n }) {
	let r = bt(), { future: i } = Dn(), { basename: a } = wn(), o = _.useMemo(() => {
		if (e === r.pathname + r.search + r.hash) return [];
		let n = mn(e, a, i.v8_trailingSlashAwareDataRequests, "rsc"), o = !1, s = [];
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
function Nn({ page: e, matches: t, ...n }) {
	let r = bt(), { future: i, manifest: a, routeModules: o } = Dn(), { basename: s } = wn(), { loaderData: c, matches: l } = Tn(), u = _.useMemo(() => yn(e, t, l, a, r, "data"), [
		e,
		t,
		l,
		a,
		r
	]), d = _.useMemo(() => yn(e, t, l, a, r, "assets"), [
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
		let d = mn(e, s, i.v8_trailingSlashAwareDataRequests, "data");
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
	]), p = _.useMemo(() => bn(d, a), [d, a]), m = jn(d);
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
function Pn(...e) {
	return (t) => {
		e.forEach((e) => {
			typeof e == "function" ? e(t) : e != null && (e.current = t);
		});
	};
}
_.Component;
var Fn = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
try {
	Fn && (window.__reactRouterVersion = "7.18.3");
} catch {}
var P = _.forwardRef(function({ onClick: e, discover: t = "render", prefetch: n = "none", relative: r, reloadDocument: i, replace: a, mask: o, state: s, target: c, to: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) {
	let { basename: h, navigator: g, useTransitions: v } = _.useContext(lt), y = typeof l == "string" && k.test(l), b = Ke(l, h);
	l = b.to;
	let x = vt(l, { relative: r }), S = bt(), C = null;
	if (o) {
		let e = Fe(o, [], S.mask ? S.mask.pathname : "/", !0);
		h !== "/" && (e.pathname = e.pathname === "/" ? h : Le([h, e.pathname])), C = g.createHref(e);
	}
	let [w, T, ee] = On(n, p), E = Bn(l, {
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
	function D(t) {
		e && e(t), t.defaultPrevented || E(t);
	}
	let O = !(b.isExternal || i), te = /* @__PURE__ */ _.createElement("a", {
		...p,
		...ee,
		href: (O ? C : void 0) || b.absoluteURL || x,
		onClick: O ? D : e,
		ref: Pn(m, T),
		target: c,
		"data-discover": !y && t === "render" ? "true" : void 0
	});
	return w && !y ? /* @__PURE__ */ _.createElement(_.Fragment, null, te, /* @__PURE__ */ _.createElement(An, { page: x })) : te;
});
P.displayName = "Link";
var In = _.forwardRef(function({ "aria-current": e = "page", caseSensitive: t = !1, className: n = "", end: r = !1, style: i, to: a, viewTransition: o, children: s, ...c }, l) {
	let u = Et(a, { relative: c.relative }), d = bt(), f = _.useContext(rt), { navigator: p, basename: m } = _.useContext(lt), h = f != null && Kn(u) && o === !0, g = p.encodeLocation ? p.encodeLocation(u).pathname : u.pathname, v = d.pathname, y = f && f.navigation && f.navigation.location ? f.navigation.location.pathname : null;
	t || (v = v.toLowerCase(), y = y ? y.toLowerCase() : null, g = g.toLowerCase()), y && m && (y = ke(y, m) || y);
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
	let ee = typeof i == "function" ? i(C) : i;
	return /* @__PURE__ */ _.createElement(P, {
		...c,
		"aria-current": w,
		className: T,
		ref: l,
		style: ee,
		to: a,
		viewTransition: o
	}, typeof s == "function" ? s(C) : s);
});
In.displayName = "NavLink";
var Ln = _.forwardRef(({ discover: e = "render", fetcherKey: t, navigate: n, reloadDocument: r, replace: i, state: a, method: o = Zt, action: s, onSubmit: c, relative: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) => {
	let { useTransitions: h } = _.useContext(lt), g = Wn(), v = Gn(s, { relative: l }), y = o.toLowerCase() === "get" ? "get" : "post", b = typeof s == "string" && k.test(s);
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
Ln.displayName = "Form";
function Rn(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function zn(e) {
	let t = _.useContext(nt);
	return A(t, Rn(e)), t;
}
function Bn(e, { target: t, replace: n, mask: r, state: i, preventScrollReset: a, relative: o, viewTransition: s, defaultShouldRevalidate: c, useTransitions: l } = {}) {
	let u = Ct(), d = bt(), f = Et(e, { relative: o });
	return _.useCallback((p) => {
		if (an(p, t)) {
			p.preventDefault();
			let t = n === void 0 ? ce(d) === ce(f) : n, m = () => u(e, {
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
function Vn(e) {
	j(typeof URLSearchParams < "u", "You cannot use the `useSearchParams` hook in a browser that does not support the URLSearchParams API. If you need to support Internet Explorer 11, we recommend you load a polyfill such as https://github.com/ungap/url-search-params.");
	let t = _.useRef(on(e)), n = _.useRef(!1), r = bt(), i = _.useMemo(() => sn(r.search, n.current ? null : t.current), [r.search]), a = Ct();
	return [i, _.useCallback((e, t) => {
		let r = on(typeof e == "function" ? e(new URLSearchParams(i)) : e);
		n.current = !0, a("?" + r, t);
	}, [a, i])];
}
var Hn = 0, Un = () => `__${String(++Hn)}__`;
function Wn() {
	let { router: e } = zn("useSubmit"), { basename: t } = _.useContext(lt), n = Vt(), r = e.fetch, i = e.navigate;
	return _.useCallback(async (e, a = {}) => {
		let { action: o, method: s, encType: c, formData: l, body: u } = fn(e, t);
		if (a.navigate === !1) {
			let e = a.fetcherKey || Un();
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
function Gn(e, { relative: t } = {}) {
	let { basename: n } = _.useContext(lt), r = _.useContext(dt);
	A(r, "useFormAction must be used inside a RouteContext");
	let [i] = r.matches.slice(-1), a = { ...Et(e || ".", { relative: t }) }, o = bt();
	if (e == null) {
		a.search = o.search;
		let e = new URLSearchParams(a.search), t = e.getAll("index");
		if (t.some((e) => e === "")) {
			e.delete("index"), t.filter((e) => e).forEach((t) => e.append("index", t));
			let n = e.toString();
			a.search = n ? `?${n}` : "";
		}
	}
	return (!e || e === ".") && i.route.index && (a.search = a.search ? a.search.replace(/^\?/, "?index&") : "?index"), n !== "/" && (a.pathname = a.pathname === "/" ? n : Le([n, a.pathname])), ce(a);
}
function Kn(e, { relative: t } = {}) {
	let n = _.useContext(ot);
	A(n != null, "`useViewTransitionState` must be used within `react-router-dom`'s `RouterProvider`.  Did you accidentally import `RouterProvider` from `react-router`?");
	let { basename: r } = zn("useViewTransitionState"), i = Et(e, { relative: t });
	if (!n.isTransitioning) return !1;
	let a = ke(n.currentLocation.pathname, r) || n.currentLocation.pathname, o = ke(n.nextLocation.pathname, r) || n.nextLocation.pathname;
	return Te(i.pathname, o) != null || Te(i.pathname, a) != null;
}
//#endregion
//#region node_modules/react/cjs/react-jsx-runtime.production.js
var qn = /* @__PURE__ */ o(((e) => {
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
	t.exports = qn();
})))(), Jn = (0, _.createContext)(null), Yn = 0;
function Xn({ children: e }) {
	let t = (0, _.useSyncExternalStore)(C, S, S), [n, r] = (0, _.useState)(t?.user.role ?? "SUPPORT"), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(!1), [f, p] = (0, _.useState)(!1), [m, h] = (0, _.useState)([]), [g, v] = (0, _.useState)({}), y = (0, _.useCallback)((e) => {
		h((t) => t.filter((t) => t.id !== e));
	}, []), b = (0, _.useCallback)((e, t, n = "blue") => {
		Yn += 1;
		let r = Yn;
		h((i) => [...i.slice(-3), {
			id: r,
			title: e,
			desc: t,
			tone: n
		}]), window.setTimeout(() => y(r), 6e3);
	}, [y]), x = (0, _.useMemo)(() => {
		let e = t?.shipments ?? [];
		return Object.keys(g).length === 0 ? e : e.map((e) => g[e.id] ?? e);
	}, [t, g]), T = (0, _.useMemo)(() => t?.contracts ?? [], [t]), ee = (0, _.useMemo)(() => t?.tasks ?? [], [t]), E = (0, _.useMemo)(() => t?.customers ?? [], [t]), D = (0, _.useMemo)(() => t?.quotes ?? [], [t]), O = (0, _.useMemo)(() => t?.agreements ?? [], [t]), k = (0, _.useMemo)(() => t?.authority ?? {
		companies: [],
		agents: []
	}, [t]), ne = (0, _.useMemo)(() => t?.notifications ?? [], [t]), re = (0, _.useMemo)(() => t?.home ?? null, [t]), ie = (0, _.useMemo)(() => t?.environment ?? null, [t]), ae = (0, _.useMemo)(() => t?.receivables ?? {
		rows: [],
		totals: {}
	}, [t]), A = (0, _.useMemo)(() => t?.payables ?? {
		rows: [],
		totals: {}
	}, [t]), j = (0, _.useMemo)(() => t?.ceoReport ?? null, [t]), oe = (0, _.useMemo)(() => t?.handbook ?? null, [t]), se = (0, _.useCallback)((e, t) => te(e, t), []), ce = (0, _.useCallback)((e, n) => {
		let r = (t?.shipments ?? []).find((t) => t.id === e) ?? Object.values(g).find((t) => t.id === e);
		if (!r) return;
		let i = n(r);
		v((t) => ({
			...t,
			[e]: i
		})), te("shipment_update", { shipment: i });
	}, [t, g]), le = t?.version, ue = (0, _.useRef)(le);
	le !== ue.current && (ue.current = le, t && v((e) => {
		let n = new Set((t.shipments ?? []).map((e) => e.id)), r = {};
		for (let [i, a] of Object.entries(e)) {
			let e = (t.shipments ?? []).find((e) => e.id === i);
			e && JSON.stringify(e) === JSON.stringify(a) || n.has(i) && (r[i] = a);
		}
		return r;
	}));
	let M = t?.user.name ?? "—", de = (0, _.useMemo)(() => ({
		role: n,
		setRole: r,
		userName: M,
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
		customers: E,
		quotes: D,
		agreements: O,
		authority: k,
		tasks: ee,
		notifications: ne,
		home: re,
		environment: ie,
		receivables: ae,
		payables: A,
		ceoReport: j,
		handbook: oe,
		unknownLabel: w(),
		dispatch: se,
		updateShipment: ce
	}), [
		n,
		M,
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
		E,
		D,
		O,
		k,
		ee,
		ne,
		re,
		ie,
		ae,
		A,
		j,
		oe,
		se,
		ce
	]);
	return /* @__PURE__ */ (0, F.jsx)(Jn.Provider, {
		value: de,
		children: e
	});
}
function Zn() {
	let e = (0, _.useContext)(Jn);
	if (!e) throw Error("useStore must be used inside <StoreProvider>");
	return e;
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toKebabCase.mjs
var Qn = (e) => e?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toLucideIconData.mjs
function $n(e, t, n = []) {
	if (t == null) throw Error("[lucide]: iconNode is required when icon name is used");
	return {
		name: Qn(e),
		size: 24,
		node: t,
		...n.length > 0 ? { aliases: n } : {}
	};
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toCamelCase.mjs
var er = (e) => {
	let t = "", n = !1;
	for (let r of e) {
		if (r === "-" || r === "_" || r <= " ") {
			n = t.length > 0;
			continue;
		}
		t.length === 0 ? t += r.toLowerCase() : t += n ? r.toUpperCase() : r, n = !1;
	}
	return t;
}, tr = (e) => {
	let t = er(e);
	return t.charAt(0).toUpperCase() + t.slice(1);
}, nr = (...e) => e.filter((e, t, n) => !!e && e.trim() !== "" && n.indexOf(e) === t).join(" ").trim(), rr = {
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
function ir(e) {
	return e != null;
}
function ar(e, t = {}) {
	let n = t.attributeNames ?? {}, r = (e) => n[e] ?? e, i = e.size ?? e.width ?? rr.width, a = e.size ?? e.height ?? rr.height, o = e.aliases?.filter((e) => typeof e == "string" && e.trim() !== "").map((e) => `lucide-${e}`) ?? [], s = [...e.name ? [`lucide-${e.name}`] : [], ...o], c = t.className?.split(" ").filter(Boolean) ?? [], l = t.includeDefaultClasses === !1 ? nr(...c) : nr("lucide", ...s, ...c), u = t.absoluteStrokeWidth ? Number(t.strokeWidth ?? rr["stroke-width"]) * Number(e.size ?? e.width ?? rr.width) / Number(t.size ?? t.width ?? rr.width) : t.strokeWidth ?? rr["stroke-width"];
	return [
		"svg",
		{
			...Object.entries(rr).reduce((e, [t, n]) => (e[r(t)] = n, e), {}),
			..."color" in t && t.color && { [r("stroke")]: t.color },
			..."size" in t && ir(t.size) && {
				[r("width")]: t.size,
				[r("height")]: t.size
			},
			..."width" in t && ir(t.width) && { [r("width")]: t.width },
			..."height" in t && ir(t.height) && { [r("height")]: t.height },
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
function or(e, t = {}) {
	return ar(e, {
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
var sr = (e) => {
	for (let t in e) if (t.startsWith("aria-") || t === "role" || t === "title") return !0;
	return !1;
}, cr = (0, _.createContext)({}), lr = () => (0, _.useContext)(cr), ur = (0, _.forwardRef)(({ color: e, size: t, width: n, height: r, strokeWidth: i, absoluteStrokeWidth: a, nonScalingStroke: o, className: s = "", children: c, iconNode: l = [], icon: u = {
	node: l,
	aliases: [],
	size: 24
}, ...d }, f) => {
	let { size: p = 24, strokeWidth: m = 2, absoluteStrokeWidth: h = !1, nonScalingStroke: g = !1, color: v = "currentColor", className: y = "" } = lr() ?? {}, b = !!c || sr(d), [x, S, C = []] = or(u, {
		color: e ?? v,
		width: n ?? t ?? p,
		height: r ?? t ?? p,
		strokeWidth: i ?? m,
		absoluteStrokeWidth: a ?? h,
		nonScalingStroke: o ?? g,
		className: nr(y, s),
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
	let r = typeof e == "string" ? $n(e, t, n) : e, i = (0, _.forwardRef)(({ className: e, ...t }, n) => (0, _.createElement)(ur, {
		ref: n,
		icon: r,
		className: e,
		...t
	}));
	return r.name && (i.displayName = tr(r.name)), i;
}
//#endregion
//#region node_modules/lucide-react/dist/esm/icons/archive.mjs
var dr = {
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
dr.node;
var fr = I(dr), pr = {
	name: "arrow-left-right",
	size: 24,
	node: [
		["path", {
			d: "M8 3 4 7l4 4",
			key: "9rb6wj"
		}],
		["path", {
			d: "M4 7h16",
			key: "6tx8e3"
		}],
		["path", {
			d: "m16 21 4-4-4-4",
			key: "siv7j2"
		}],
		["path", {
			d: "M20 17H4",
			key: "h6l3hr"
		}]
	]
};
pr.node;
var mr = I(pr), hr = {
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
hr.node;
var gr = I(hr), _r = {
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
_r.node;
var vr = I(_r), yr = {
	name: "arrow-up-right",
	size: 24,
	node: [["path", {
		d: "M7 7h10v10",
		key: "1tivn9"
	}], ["path", {
		d: "M7 17 17 7",
		key: "1vkiza"
	}]]
};
yr.node;
var br = I(yr), xr = {
	name: "badge-check",
	size: 24,
	node: [["path", {
		d: "M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z",
		key: "3c2336"
	}], ["path", {
		d: "m16 9-5.5 5.5L8 12",
		key: "xofnsj"
	}]],
	aliases: ["verified"]
};
xr.node;
var Sr = I(xr), Cr = {
	name: "ban",
	size: 24,
	node: [["circle", {
		cx: "12",
		cy: "12",
		r: "10",
		key: "1mglay"
	}], ["path", {
		d: "M4.929 4.929 19.07 19.071",
		key: "196cmz"
	}]]
};
Cr.node;
var wr = I(Cr), Tr = {
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
Tr.node;
var Er = I(Tr), Dr = {
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
Dr.node;
var Or = I(Dr), kr = {
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
kr.node;
var Ar = I(kr), jr = {
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
jr.node;
var Mr = I(jr), Nr = {
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
Nr.node;
var Pr = I(Nr), Fr = {
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
Fr.node;
var Ir = I(Fr), Lr = {
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
Lr.node;
var Rr = I(Lr), zr = {
	name: "check",
	size: 24,
	node: [["path", {
		d: "M20 6 9 17l-5-5",
		key: "1gmf2c"
	}]]
};
zr.node;
var Br = I(zr), Vr = {
	name: "chevron-right",
	size: 24,
	node: [["path", {
		d: "m9 18 6-6-6-6",
		key: "mthhwq"
	}]]
};
Vr.node;
var Hr = I(Vr), Ur = {
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
Ur.node;
var Wr = I(Ur), Gr = {
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
Gr.node;
var Kr = I(Gr), qr = {
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
qr.node;
var Jr = I(qr), Yr = {
	name: "circle-user-round",
	size: 24,
	node: [
		["path", {
			d: "M17.925 20.056a6 6 0 0 0-11.851.001",
			key: "z69sun"
		}],
		["circle", {
			cx: "12",
			cy: "11",
			r: "4",
			key: "1gt34v"
		}],
		["circle", {
			cx: "12",
			cy: "12",
			r: "10",
			key: "1mglay"
		}]
	],
	aliases: ["user-circle-2"]
};
Yr.node;
var Xr = I(Yr), Zr = {
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
Zr.node;
var Qr = I(Zr), $r = {
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
$r.node;
var ei = I($r), ti = {
	name: "copy",
	size: 24,
	node: [["rect", {
		width: "14",
		height: "14",
		x: "8",
		y: "8",
		rx: "2",
		ry: "2",
		key: "17jyea"
	}], ["path", {
		d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",
		key: "zix9uf"
	}]]
};
ti.node;
var ni = I(ti), ri = {
	name: "database",
	size: 24,
	node: [
		["ellipse", {
			cx: "12",
			cy: "5",
			rx: "9",
			ry: "3",
			key: "msslwz"
		}],
		["path", {
			d: "M3 5V19A9 3 0 0 0 21 19V5",
			key: "1wlel7"
		}],
		["path", {
			d: "M3 12A9 3 0 0 0 21 12",
			key: "mv7ke4"
		}]
	]
};
ri.node;
var ii = I(ri), ai = {
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
ai.node;
var oi = I(ai), si = {
	name: "eraser",
	size: 24,
	node: [["path", {
		d: "M21 21H8a2 2 0 0 1-1.42-.587l-3.994-3.999a2 2 0 0 1 0-2.828l10-10a2 2 0 0 1 2.829 0l5.999 6a2 2 0 0 1 0 2.828L12.834 21",
		key: "g5wo59"
	}], ["path", {
		d: "m5.082 11.09 8.828 8.828",
		key: "1wx5vj"
	}]]
};
si.node;
var ci = I(si), li = {
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
li.node;
var ui = I(li), di = {
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
di.node;
var fi = I(di), pi = {
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
pi.node;
var mi = I(pi), hi = {
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
hi.node;
var gi = I(hi), _i = {
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
_i.node;
var vi = I(_i), yi = {
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
yi.node;
var bi = I(yi), xi = {
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
xi.node;
var Si = I(xi), Ci = {
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
Ci.node;
var wi = I(Ci), Ti = {
	name: "key-round",
	size: 24,
	node: [["path", {
		d: "M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z",
		key: "1s6t7t"
	}], ["circle", {
		cx: "16.5",
		cy: "7.5",
		r: ".5",
		fill: "currentColor",
		key: "w0ekpg"
	}]]
};
Ti.node;
var Ei = I(Ti), Di = {
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
Di.node;
var Oi = I(Di), ki = {
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
ki.node;
var Ai = I(ki), ji = {
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
ji.node;
var Mi = I(ji), Ni = {
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
Ni.node;
var Pi = I(Ni), Fi = {
	name: "loader-circle",
	size: 24,
	node: [["path", {
		d: "M21 12a9 9 0 1 1-6.219-8.56",
		key: "13zald"
	}]],
	aliases: ["loader-2"]
};
Fi.node;
var Ii = I(Fi), L = {
	name: "lock",
	size: 24,
	node: [["rect", {
		width: "18",
		height: "11",
		x: "3",
		y: "11",
		rx: "2",
		ry: "2",
		key: "1w4ew1"
	}], ["path", {
		d: "M7 11V7a5 5 0 0 1 10 0v4",
		key: "fwvmzm"
	}]]
};
L.node;
var Li = I(L), Ri = {
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
Ri.node;
var zi = I(Ri), Bi = {
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
Bi.node;
var Vi = I(Bi), Hi = {
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
Hi.node;
var Ui = I(Hi), Wi = {
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
Wi.node;
var Gi = I(Wi), Ki = {
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
Ki.node;
var qi = I(Ki), Ji = {
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
Ji.node;
var Yi = I(Ji), Xi = {
	name: "phone",
	size: 24,
	node: [["path", {
		d: "M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384",
		key: "9njp5v"
	}]]
};
Xi.node;
var Zi = I(Xi), Qi = {
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
Qi.node;
var $i = I(Qi), ea = {
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
ea.node;
var ta = I(ea), na = {
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
na.node;
var R = I(na), ra = {
	name: "shield-alert",
	size: 24,
	node: [
		["path", {
			d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
			key: "oel41y"
		}],
		["path", {
			d: "M12 8v4",
			key: "1got3b"
		}],
		["path", {
			d: "M12 16h.01",
			key: "1drbdi"
		}]
	]
};
ra.node;
var ia = I(ra), aa = {
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
aa.node;
var oa = I(aa), sa = {
	name: "shield-question-mark",
	size: 24,
	node: [
		["path", {
			d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
			key: "oel41y"
		}],
		["path", {
			d: "M9.1 9a3 3 0 0 1 5.82 1c0 2-3 3-3 3",
			key: "mhlwft"
		}],
		["path", {
			d: "M12 17h.01",
			key: "p32p05"
		}]
	],
	aliases: ["shield-question"]
};
sa.node;
var ca = I(sa), la = {
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
la.node;
var ua = I(la), da = {
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
da.node;
var fa = I(da), pa = {
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
pa.node;
var ma = I(pa), ha = {
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
ha.node;
var ga = I(ha), _a = {
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
_a.node;
var va = I(_a), ya = {
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
ya.node;
var ba = I(ya), xa = {
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
xa.node;
var Sa = I(xa), Ca = {
	name: "user-cog",
	size: 24,
	node: [
		["path", {
			d: "M10 15H6a4 4 0 0 0-4 4v2",
			key: "1nfge6"
		}],
		["path", {
			d: "m14.305 16.53.923-.382",
			key: "1itpsq"
		}],
		["path", {
			d: "m15.228 13.852-.923-.383",
			key: "eplpkm"
		}],
		["path", {
			d: "m16.852 12.228-.383-.923",
			key: "13v3q0"
		}],
		["path", {
			d: "m16.852 17.772-.383.924",
			key: "1i8mnm"
		}],
		["path", {
			d: "m19.148 12.228.383-.923",
			key: "1q8j1v"
		}],
		["path", {
			d: "m19.53 18.696-.382-.924",
			key: "vk1qj3"
		}],
		["path", {
			d: "m20.772 13.852.924-.383",
			key: "n880s0"
		}],
		["path", {
			d: "m20.772 16.148.924.383",
			key: "1g6xey"
		}],
		["circle", {
			cx: "18",
			cy: "15",
			r: "3",
			key: "gjjjvw"
		}],
		["circle", {
			cx: "9",
			cy: "7",
			r: "4",
			key: "nufk8"
		}]
	]
};
Ca.node;
var wa = I(Ca), Ta = {
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
Ta.node;
var Ea = I(Ta), Da = {
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
Da.node;
var Oa = I(Da), ka = {
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
ka.node;
var Aa = I(ka), ja = {
	ADMIN: "Quản trị",
	SUPPORT: "Điều phối",
	SALE: "Kinh doanh"
}, Ma = [
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
], Na = {
	shipments: [],
	contracts: [],
	customers: [],
	quotes: [],
	tasks: [],
	notifs: []
};
function Pa(e, t) {
	e.length = 0, Array.isArray(t) && e.push(...t);
}
C(() => {
	let e = S();
	e && (Pa(Na.shipments, e.shipments), Pa(Na.contracts, e.contracts), Pa(Na.customers, e.customers), Pa(Na.quotes, e.quotes), Pa(Na.tasks, e.tasks), Pa(Na.notifs, e.notifications));
});
{
	let e = S();
	e && (Pa(Na.shipments, e.shipments), Pa(Na.contracts, e.contracts), Pa(Na.customers, e.customers), Pa(Na.quotes, e.quotes), Pa(Na.tasks, e.tasks), Pa(Na.notifs, e.notifications));
}
var Fa = Na.shipments, Ia = Na.contracts, La = Na.customers, Ra = Na.quotes, za = Na.tasks;
Na.notifs;
//#endregion
//#region src/lib/format.ts
function z(...e) {
	return e.filter(Boolean).join(" ");
}
function Ba(e) {
	return e == null || e === "" || typeof e == "number" && Number.isNaN(e);
}
function Va(e, t) {
	if (Ba(e)) return "—";
	let n = Number(e);
	return Number.isNaN(n) ? "—" : n.toLocaleString("vi-VN");
}
function Ha(e) {
	return Ba(e) ? "— ₫" : `${Va(e)} ₫`;
}
function B(e, t) {
	let n = (t || "VND").toUpperCase();
	return Ba(e) ? `— ${n}` : `${Va(e)} ${n}`;
}
function Ua(e, t) {
	let n = (t || "VND").toUpperCase();
	return Ba(e) ? `— tr ${n}` : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr ${n}`;
}
function Wa(e) {
	return Ba(e) ? "—" : `${Number(e).toLocaleString("vi-VN", { maximumFractionDigits: 2 })}%`;
}
function Ga(e) {
	return Ba(e) ? "— tr" : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr`;
}
function Ka(e) {
	if (Ba(e)) return "—";
	let t = Number(e);
	return Number.isNaN(t) ? String(e) : t.toLocaleString("vi-VN");
}
function V(e) {
	let t = (e ?? "").trim();
	return t.length > 0 ? t : "—";
}
function qa(e, t, n) {
	if (!t) return;
	let r = atob(t), i = new Uint8Array(r.length);
	for (let e = 0; e < r.length; e += 1) i[e] = r.charCodeAt(e);
	let a = new Blob([i], { type: n }), o = URL.createObjectURL(a), s = document.createElement("a");
	s.href = o, s.download = e, document.body.appendChild(s), s.click(), document.body.removeChild(s), setTimeout(() => URL.revokeObjectURL(o), 4e3);
}
//#endregion
//#region src/components/ui.tsx
var Ja = {
	layout: Ai,
	alarm: Or,
	box: qi,
	plus: Jr,
	truck: ba,
	users: Ea,
	handshake: Si,
	calc: Ir,
	filecheck: mi,
	filetext: bi,
	wallet: Oa,
	scale: ta,
	building: Pr,
	chart: Rr,
	search: R,
	book: Mr,
	lang: Oi,
	shield: oa
};
function H({ tone: e, children: t, size: n = "md" }) {
	return /* @__PURE__ */ (0, F.jsx)("span", {
		className: z("inline-flex items-center gap-1.5 font-semibold border rounded-full whitespace-nowrap", n === "sm" ? "text-[12.5px] px-2.5 py-1" : "text-[13.5px] px-3 py-1.5", {
			green: "bg-emerald-50 text-emerald-800 border-emerald-200",
			amber: "bg-amber-50 text-amber-900 border-amber-200",
			red: "bg-red-50 text-red-800 border-red-200",
			blue: "bg-blue-50 text-blue-800 border-blue-200",
			gray: "bg-slate-100 text-slate-700 border-slate-200"
		}[e]),
		children: t
	});
}
function Ya({ tone: e }) {
	return /* @__PURE__ */ (0, F.jsx)("span", { className: z("inline-block w-2.5 h-2.5 rounded-full shrink-0", {
		green: "bg-emerald-500",
		amber: "bg-amber-500",
		red: "bg-red-500",
		blue: "bg-blue-500",
		gray: "bg-slate-400"
	}[e] ?? "bg-slate-400") });
}
function U({ icon: e, title: t, sub: n, right: r }) {
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
function W({ label: e, required: t, hint: n, error: r, children: i }) {
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
var G = (e) => z("w-full rounded-xl border-2 bg-white px-3.5 text-[15.5px] min-h-[48px] py-2.5 placeholder:text-slate-400 transition-colors", e === "missing" && "border-amber-400 bg-amber-50/60", e === "invalid" && "border-red-400 bg-red-50/60", (!e || e === "ok") && "border-slate-200 focus:border-[#1e5aa8]");
function Xa({ children: e, onClick: t, className: n, disabled: r }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		disabled: r,
		className: z("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] hover:bg-[#14365e] text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-navy-900/20 disabled:opacity-50 disabled:cursor-not-allowed", n),
		children: e
	});
}
function Za({ children: e, onClick: t, className: n }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		className: z("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-emerald-600/25", n),
		children: e
	});
}
function Qa({ children: e, onClick: t, className: n, danger: r }) {
	return /* @__PURE__ */ (0, F.jsx)("button", {
		onClick: t,
		className: z("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 font-semibold text-[15px] px-4 min-h-[48px] bg-white", r ? "border-red-200 text-red-700 hover:bg-red-50" : "border-slate-200 text-[#0f2a4a] hover:bg-slate-50", n),
		children: e
	});
}
function $a({ tone: e = "amber", title: t, desc: n, action: r, onAction: i }) {
	let a = {
		amber: "border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50/60",
		red: "border-red-300 bg-gradient-to-r from-red-50 to-orange-50/60",
		green: "border-emerald-300 bg-gradient-to-r from-emerald-50 to-teal-50/60",
		blue: "border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50/60"
	}, o = e === "red" ? Ui : e === "green" ? Kr : e === "blue" ? wi : va, s = e === "red" ? "bg-red-600" : e === "green" ? "bg-emerald-600" : e === "blue" ? "bg-blue-600" : "bg-amber-500";
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: z("rounded-2xl border-2 p-4 md:p-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-4", a[e]),
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-3 flex-1 min-w-0",
			children: [/* @__PURE__ */ (0, F.jsx)("span", {
				className: z("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", s),
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
				/* @__PURE__ */ (0, F.jsx)(vr, { size: 18 })
			]
		})]
	});
}
function eo({ what: e, where: t, actionLabel: n, onAction: r }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-xl border-2 border-dashed border-amber-400 bg-amber-50 p-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-2 flex-1",
			children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
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
				/* @__PURE__ */ (0, F.jsx)(Yi, { size: 16 }),
				" ",
				n
			]
		})]
	});
}
function to({ label: e, value: t, big: n }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "flex items-start justify-between gap-3 py-2 border-b border-slate-100 last:border-0",
		children: [/* @__PURE__ */ (0, F.jsx)("span", {
			className: "text-[13.5px] text-slate-500 font-medium shrink-0 pt-0.5",
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("span", {
			className: z("text-right font-semibold text-slate-800", n ? "text-[17px]" : "text-[14.5px]"),
			children: t
		})]
	});
}
//#endregion
//#region src/components/Layout.tsx
function no() {
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
function ro({ children: e }) {
	let { role: t, setRole: n, userName: r, query: i, setQuery: a, searchOpen: o, setSearchOpen: s, navOpen: c, setNavOpen: l, notifOpen: u, setNotifOpen: d, quickAddOpen: f, setQuickAddOpen: p, toasts: m, dismissToast: h, toast: g, notifications: v, tasks: y, environment: b } = Zn(), x = v, S = x.length, C = y.filter((e) => e.level === "Khan" || e.level === "CanXuLy").length, w = Ct(), T = bt(), [ee, E] = (0, _.useState)(!1), D = (0, _.useMemo)(() => {
		let e = i.trim().toLowerCase();
		return e.length < 2 ? null : {
			lots: Fa.filter((t) => (t.id + t.customer + t.contract + t.route).toLowerCase().includes(e)).slice(0, 4),
			cts: Ia.filter((t) => (t.id + t.company + t.agent).toLowerCase().includes(e)).slice(0, 3),
			cus: La.filter((t) => (t.name + t.mst).toLowerCase().includes(e)).slice(0, 3),
			quo: Ra.filter((t) => (t.id + t.customer).toLowerCase().includes(e)).slice(0, 2)
		};
	}, [i]), O = (e) => {
		s(!1), a(""), w(e), l(!1);
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
							children: /* @__PURE__ */ (0, F.jsx)(Vi, {
								size: 22,
								className: "text-[#0f2a4a]"
							})
						}),
						/* @__PURE__ */ (0, F.jsx)(no, {}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "hidden md:flex flex-1 max-w-[560px] mx-auto relative",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center w-full rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
								children: [
									/* @__PURE__ */ (0, F.jsx)(R, {
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
										children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 16 })
									})
								]
							}), o && D && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "absolute top-[52px] left-0 right-0 bg-white rounded-2xl border border-slate-200 shadow-2xl p-2 z-50 anim-slide-up max-h-[70vh] overflow-auto",
								children: [
									D.lots.length + D.cts.length + D.cus.length + D.quo.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "p-4 text-[14.5px] text-slate-500",
										children: [
											"Không tìm thấy “",
											i,
											"”. Thử lại theo ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "mã lô" }),
											", ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "tên khách hàng" }),
											" hoặc ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: "số hợp đồng" }),
											" đang có trong hệ thống."
										]
									}),
									D.lots.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => O(`/lo-hang/${e.id}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-blue-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(qi, {
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
									D.cts.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => O(`/hop-dong/${e.id}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-emerald-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(bi, {
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
									D.cus.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => O("/khach-hang"),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-amber-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(ba, {
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
									D.quo.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => O("/kinh-doanh-bao-gia"),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-violet-100 grid place-items-center",
											children: /* @__PURE__ */ (0, F.jsx)(Ir, {
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
							children: /* @__PURE__ */ (0, F.jsx)(R, {
								size: 21,
								className: "text-[#0f2a4a]"
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "relative hidden sm:block",
							children: [/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => E((e) => !e),
								className: "flex items-center gap-2 rounded-xl border-2 border-slate-200 pl-1.5 pr-2.5 py-1 hover:border-[#1e5aa8]",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: z("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", t === "ADMIN" ? "bg-violet-600" : t === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600"),
									children: r.charAt(0)
								}), /* @__PURE__ */ (0, F.jsxs)("span", {
									className: "text-left leading-tight",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[13px] font-bold text-[#0f2a4a]",
										children: r
									}), /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block text-[11.5px] text-slate-500",
										children: [
											ja[t],
											" · ",
											t
										]
									})]
								})]
							}), ee && /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "absolute right-0 top-[52px] w-[260px] bg-white rounded-2xl border shadow-2xl p-2 z-50 anim-slide-up",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "px-3 pt-2 pb-1 text-[12px] font-bold uppercase tracking-wide text-slate-400",
									children: "Xem giao diện theo vai trò — chỉ thay hiển thị, quyền thật theo tài khoản đăng nhập"
								}), [
									"ADMIN",
									"SUPPORT",
									"SALE"
								].map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => {
										n(e), E(!1), g(`Đã chuyển sang vai trò ${ja[e]}`, e === "ADMIN" ? "Xem được hợp đồng, tài chính & người dùng" : e === "SUPPORT" ? "Ưu tiên điều phối lô hàng & chứng từ" : "Ưu tiên khách hàng, báo giá & hợp đồng", "blue");
									},
									className: z("w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between hover:bg-slate-50", t === e && "bg-blue-50"),
									children: [/* @__PURE__ */ (0, F.jsxs)("span", { children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "block font-bold text-[14.5px]",
										children: ja[e]
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
							children: [/* @__PURE__ */ (0, F.jsx)(Ar, {
								size: 21,
								className: "text-[#0f2a4a]"
							}), S > 0 && /* @__PURE__ */ (0, F.jsx)("span", {
								className: "absolute top-1 right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-600 text-white text-[11px] font-extrabold grid place-items-center",
								children: S
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => p(!0),
							className: "hidden md:inline-flex touch-target items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px] hover:bg-[#14365e]",
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 18 }), " Thêm"]
						})
					]
				}), o && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "md:hidden px-3 pb-3 anim-slide-up",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center rounded-xl border-2 border-[#1e5aa8] bg-slate-50",
						children: [
							/* @__PURE__ */ (0, F.jsx)(R, {
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
								children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 18 })
							})
						]
					}), D && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-2 bg-white rounded-2xl border shadow-xl divide-y max-h-[50vh] overflow-auto",
						children: [
							D.lots.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => O(`/lo-hang/${e.id}`),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, F.jsx)(qi, {
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
							D.cts.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => O(`/hop-dong/${e.id}`),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, F.jsx)(bi, {
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
							D.lots.length + D.cts.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "p-4 text-[14px] text-slate-500",
								children: "Không tìm thấy. Thử lại theo mã lô, tên khách hàng hoặc số hợp đồng."
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
							children: [Ma.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "mb-4",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "px-3 mb-1.5 text-[11.5px] font-extrabold tracking-wider text-slate-400",
									children: e.group
								}), e.items.map((e) => {
									let t = Ja[e.icon] ?? qi;
									return /* @__PURE__ */ (0, F.jsxs)(In, {
										to: e.to,
										className: ({ isActive: t }) => z("flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14.5px] font-medium mb-0.5 transition-colors", t || e.to !== "/" && T.pathname.startsWith(e.to) ? "bg-[#0f2a4a] text-white shadow-md" : "text-slate-700 hover:bg-slate-100"),
										children: [
											/* @__PURE__ */ (0, F.jsx)(t, {
												size: 19,
												className: "shrink-0"
											}),
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "flex-1",
												children: e.label
											}),
											e.to === "/viec-can-xu-ly" && C > 0 && /* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
												children: C
											}),
											e.soon && /* @__PURE__ */ (0, F.jsx)("span", {
												className: "text-[10.5px] font-extrabold uppercase tracking-wide rounded-full border border-slate-300 bg-slate-100 text-slate-500 px-2 py-0.5",
												children: "Sắp có"
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
										children: "Sổ tay tra cứu quy trình, chứng từ và phân quyền cho Sale & Support."
									}),
									/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/so-tay",
										className: "mt-2.5 inline-flex items-center gap-1.5 bg-white text-[#0f2a4a] text-[13.5px] font-bold rounded-lg px-3 py-2",
										children: ["Mở sổ tay ", /* @__PURE__ */ (0, F.jsx)(Hr, { size: 15 })]
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
									children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 20 })
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
											className: z("flex-1 touch-target rounded-xl border-2 text-[13px] font-bold py-2", t === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600"),
											children: e
										}, e))
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "px-2 text-[12px] text-slate-500 mb-2",
										children: [
											"Đang dùng: ",
											/* @__PURE__ */ (0, F.jsx)("b", { children: r }),
											" · ",
											ja[t]
										]
									}),
									Ma.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
										className: "mb-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "px-2 mb-1 text-[11px] font-extrabold tracking-wider text-slate-400",
											children: e.group
										}), e.items.map((e) => {
											let t = Ja[e.icon] ?? qi, n = e.to === "/" ? T.pathname === "/" : T.pathname.startsWith(e.to);
											return /* @__PURE__ */ (0, F.jsxs)(In, {
												to: e.to,
												onClick: () => l(!1),
												className: z("flex items-center gap-3 px-3 py-3 rounded-xl text-[15px] font-medium mb-0.5", n ? "bg-[#0f2a4a] text-white" : "text-slate-700 hover:bg-slate-100"),
												children: [
													/* @__PURE__ */ (0, F.jsx)(t, {
														size: 20,
														className: "shrink-0"
													}),
													e.label,
													e.to === "/viec-can-xu-ly" && C > 0 && /* @__PURE__ */ (0, F.jsx)("span", {
														className: "ml-auto text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
														children: C
													}),
													e.soon && /* @__PURE__ */ (0, F.jsx)("span", {
														className: "ml-auto text-[10.5px] font-extrabold uppercase tracking-wide rounded-full border border-slate-300 bg-slate-100 text-slate-500 px-2 py-0.5",
														children: "Sắp có"
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
						children: [e, /* @__PURE__ */ (0, F.jsxs)("footer", {
							className: "mt-10 text-center text-[12.5px] text-slate-400 pb-4",
							children: ["CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam · ", b?.isSandbox ? "Bản nội bộ — môi trường staging cách ly, mọi ghi nhận đi qua writer/RBAC/audit thật" : "Bản nội bộ — dữ liệu thật từ hệ thống Logistics, cập nhật liên tục"]
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
							icon: Ja.layout
						},
						{
							to: "/lo-hang",
							label: "Lô hàng",
							icon: qi
						},
						{
							to: "/hop-dong",
							label: "Hợp đồng",
							icon: bi
						},
						{
							to: "/tai-chinh/thu-tien",
							label: "Tài chính",
							icon: Oa
						}
					].map((e) => {
						let t = e.to === "/" ? T.pathname === "/" : T.pathname.startsWith(e.to), n = e.icon;
						return /* @__PURE__ */ (0, F.jsxs)(In, {
							to: e.to,
							className: z("touch-target flex flex-col items-center justify-center gap-0.5 py-2 text-[11.5px] font-semibold", t ? "text-[#0f2a4a]" : "text-slate-400"),
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
							children: /* @__PURE__ */ (0, F.jsx)($i, { size: 22 })
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
									S,
									" chưa đọc"
								]
							}), /* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => d(!1),
								className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
								children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 20 })
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex-1 overflow-y-auto p-3 space-y-2",
							children: [x.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[14px] text-slate-500 p-4 text-center",
								children: "Không có cảnh báo nào theo dữ liệu hiện tại."
							}), x.map((e) => /* @__PURE__ */ (0, F.jsx)("div", {
								className: "rounded-2xl border border-slate-200 p-3.5 lift",
								children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex items-start gap-2.5",
									children: [/* @__PURE__ */ (0, F.jsx)("span", { className: z("w-2.5 h-2.5 rounded-full mt-1.5 shrink-0", e.tone === "red" ? "bg-red-500 pulse-dot" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500") }), /* @__PURE__ */ (0, F.jsxs)("div", { children: [
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
									d(!1), w("/viec-can-xu-ly");
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
								children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 20 })
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
									icon: qi,
									bg: "bg-blue-50 text-blue-700"
								},
								{
									label: "Tạo hợp đồng mới",
									desc: "HDMB / HDNT + phụ lục",
									to: "/hop-dong/moi",
									icon: bi,
									bg: "bg-emerald-50 text-emerald-700"
								},
								{
									label: "Tạo báo giá",
									desc: "Dự toán chi phí & giá bán",
									to: "/kinh-doanh-bao-gia",
									icon: Ir,
									bg: "bg-violet-50 text-violet-700"
								},
								{
									label: "Ghi nhận thanh toán",
									desc: "Thu tiền khách / trả đối tác",
									to: "/tai-chinh/thu-tien",
									icon: Oa,
									bg: "bg-amber-50 text-amber-700"
								},
								{
									label: "Tra cứu thuế / HS",
									desc: "Mã HS & mô tả hàng hóa",
									to: "/tra-cuu-thue",
									icon: ba,
									bg: "bg-slate-100 text-slate-700"
								}
							].map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => {
									p(!1), w(e.to);
								},
								className: "touch-target flex items-center gap-3 rounded-2xl border-2 border-slate-100 hover:border-[#1e5aa8] p-3.5 text-left lift bg-white",
								children: [
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: z("w-11 h-11 rounded-xl grid place-items-center shrink-0", e.bg),
										children: /* @__PURE__ */ (0, F.jsx)(e.icon, { size: 21 })
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "flex-1",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "font-bold text-[15px] text-[#0f2a4a] flex items-center gap-2",
											children: e.label
										}), /* @__PURE__ */ (0, F.jsx)("span", {
											className: "block text-[13px] text-slate-500",
											children: e.desc
										})]
									}),
									/* @__PURE__ */ (0, F.jsx)(Hr, {
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
							className: z("w-9 h-9 rounded-xl grid place-items-center shrink-0", e.tone === "green" ? "bg-emerald-500" : e.tone === "red" ? "bg-red-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500"),
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
							children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 16 })
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
var io = {
	"Lô đang chạy": {
		icon: ba,
		bg: "bg-slate-600",
		bar: "bg-slate-500"
	},
	"Chờ lấy hàng": {
		icon: Gi,
		bg: "bg-slate-600",
		bar: "bg-slate-500"
	},
	"Đang vận chuyển": {
		icon: ba,
		bg: "bg-blue-600",
		bar: "bg-blue-500"
	},
	"Chờ thông quan": {
		icon: mi,
		bg: "bg-amber-500",
		bar: "bg-amber-500"
	},
	"Chờ giao": {
		icon: Gi,
		bg: "bg-blue-600",
		bar: "bg-blue-500"
	},
	"Đã giao": {
		icon: mi,
		bg: "bg-emerald-600",
		bar: "bg-emerald-500"
	}
}, ao = {
	icon: vi,
	bg: "bg-red-500",
	bar: "bg-red-500"
};
function oo() {
	let { shipments: e, home: t, tasks: n, environment: r } = Zn(), i = Ct(), a = t?.tiles ?? [], o = t?.focus ?? null, s = t?.summary, c = (n ?? []).slice(0, 3), l = t?.runningSummary ?? [], u = (/* @__PURE__ */ new Date()).toLocaleDateString("vi-VN", {
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
							children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 18 })]
						}), o && /* @__PURE__ */ (0, F.jsxs)(P, {
							to: `/lo-hang/${o.id}`,
							className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]",
							children: ["Mở ", o.id]
						})]
					})
				]
			}),
			o && /* @__PURE__ */ (0, F.jsx)($a, {
				tone: o.priority === "Khan" ? "red" : "amber",
				title: `${o.id}: ${o.nextAction}`,
				desc: V(o.nextActionDetail),
				action: "XỬ LÝ NGAY",
				onAction: () => {
					i(o.to);
				}
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", { children: [/* @__PURE__ */ (0, F.jsx)(U, {
				title: "VIỆC TIẾP THEO",
				sub: "Bấm vào từng thẻ để đi thẳng tới màn hình xử lý"
			}), /* @__PURE__ */ (0, F.jsx)("div", {
				className: "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3",
				children: a.map((e) => {
					let t = io[e.label] ?? ao, n = t.icon;
					return /* @__PURE__ */ (0, F.jsxs)(P, {
						to: e.to,
						className: "lift btn-press rounded-2xl bg-white border border-slate-200 overflow-hidden flex sm:flex-col min-h-[88px]",
						children: [/* @__PURE__ */ (0, F.jsx)("div", { className: z("w-1.5 sm:w-full sm:h-1.5 shrink-0", t.bar) }), /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "p-3.5 flex items-center sm:items-start gap-3 sm:flex-col sm:gap-2 flex-1",
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: z("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", t.bg),
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
										children: ["Xem lô ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
									})
								]
							})]
						})]
					}, e.label);
				})
			})] }),
			/* @__PURE__ */ (0, F.jsxs)("section", { children: [/* @__PURE__ */ (0, F.jsx)(U, {
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
								children: Ga(t?.outstandingTotal)
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
							children: [/* @__PURE__ */ (0, F.jsx)(Qr, {
								size: 19,
								className: "text-red-600"
							}), " Quá hạn và sắp tới hạn"]
						}), /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/viec-can-xu-ly",
							className: "text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
							children: ["Tất cả ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
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
								/* @__PURE__ */ (0, F.jsx)("span", { className: z("w-2.5 h-10 rounded-full shrink-0", e.statusTone === "red" ? "bg-red-500" : e.statusTone === "amber" ? "bg-amber-500" : e.statusTone === "blue" ? "bg-blue-500" : "bg-slate-400") }),
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
									children: ["Xử lý ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
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
								children: ["Tất cả lô ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
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
										/* @__PURE__ */ (0, F.jsx)(Ya, { tone: n?.statusTone ?? "gray" }),
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
							children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
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
						children: ["Mở tài chính ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
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
										Ga(t?.outstandingTotal),
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
var K = {
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
function q() {
	let [e, t] = (0, _.useState)("ALL"), [n, r] = (0, _.useState)(""), i = (0, _.useMemo)(() => za.filter((t) => (e === "ALL" || t.level === e) && (!n || (t.lot + t.customer + t.job + t.assignee).toLowerCase().includes(n.toLowerCase()))), [e, n]), a = (0, _.useMemo)(() => ({
		ALL: za.length,
		Khan: za.filter((e) => e.level === "Khan").length,
		CanXuLy: za.filter((e) => e.level === "CanXuLy").length,
		BinhThuong: za.filter((e) => e.level === "BinhThuong").length
	}), [za.length, za]);
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [/* @__PURE__ */ (0, F.jsx)(U, {
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
							className: z("touch-target shrink-0 rounded-xl border-2 px-4 min-h-[48px] text-[14.5px] font-bold", e === n ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
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
									className: z("inline-flex items-center gap-1.5 text-[12.5px] font-extrabold rounded-full px-2.5 py-1 whitespace-nowrap", K[e.level].cls),
									children: K[e.level].label
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
									children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
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
									className: z("inline-flex items-center text-[12px] font-extrabold rounded-full px-2.5 py-1", K[e.level].cls),
									children: K[e.level].label
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
							children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 18 })]
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
				children: [/* @__PURE__ */ (0, F.jsx)(Pi, {
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
function so() {
	let { shipments: e } = Zn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)("ALL"), [a, o] = (0, _.useState)(!1), s = (0, _.useMemo)(() => e.filter((e) => (r === "ALL" || e.status === r) && (!t || (e.id + e.customer + e.contract + e.route + e.sale + e.support).toLowerCase().includes(t.toLowerCase()))), [
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
					/* @__PURE__ */ (0, F.jsx)(U, {
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
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
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
							className: z("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", a ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, F.jsx)(ua, { size: 18 }),
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
							className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", r === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
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
										children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }), " 360°"]
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
									/* @__PURE__ */ (0, F.jsx)(Ya, { tone: e.statusTone }),
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
							children: ["XỬ LÝ ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
						}), /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/lo-hang/" + e.id,
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 17 }), " XEM 360°"]
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
var co = [
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
function lo() {
	let { id: e } = Tt(), [t, n] = Vn(), r = t.get("tab") || "lay-hang", { shipments: i, updateShipment: a, toast: o, contracts: s, dispatch: c } = Zn(), l = Ct(), u = i.find((t) => t.id === e), [d, f] = (0, _.useState)(!1), [p, m] = (0, _.useState)(!1), [h, g] = (0, _.useState)(""), [v, y] = (0, _.useState)("Thu tiền khách"), [b, x] = (0, _.useState)(""), [S, C] = (0, _.useState)({
		name: "",
		qty: "1",
		price: "",
		cost: "",
		vat: "8"
	}), [w, T] = (0, _.useState)({}), [ee, E] = (0, _.useState)(0);
	(0, _.useEffect)(() => {
		T({}), C({
			name: "",
			qty: "1",
			price: "",
			cost: "",
			vat: "8"
		}), x("");
	}, [e, r]);
	let D = (e, t) => T((n) => ({
		...n,
		[e]: t
	})), O = (e, t) => w[e] ?? t, te = (0, _.useMemo)(() => s.find((e) => e.id === u?.contract), [s, u]);
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
	let k = u.finance.currency || "VND", ne = (e) => {
		let t = {};
		for (let [n, r] of Object.entries(e)) {
			let e = (r ?? "").trim();
			e.length > 0 && (t[n] = e);
		}
		return t;
	}, re = (e, t = []) => {
		T((e) => {
			if (t.length === 0) return {};
			let n = {};
			for (let r of t) e[r] != null && (n[r] = e[r]);
			return n;
		}), E(Date.now()), o(e, "Đã gửi tới backend. Dữ liệu sẽ được đọc lại từ Logistics sau khi ghi.", "green");
	}, ie = () => {
		let e = {
			...ne({
				container_no: O("plate", u.pickup.plate),
				etd: O("pickupTime", u.pickup.pickupTime),
				booking_no: O("bookingNo", u.transport?.bookingNo ?? ""),
				carrier: O("carrier", u.transport?.carrier ?? ""),
				pol: O("pol", u.transport?.pol ?? ""),
				pod: O("pod", u.transport?.pod ?? ""),
				qty_pkg: O("qtyPkg", u.transport?.qtyPkg ?? "")
			}),
			...w.truckType == null ? {} : { pickup_truck_type: w.truckType.trim() }
		};
		if (Object.keys(e).length === 0) {
			o("Chưa có gì để lưu", "Nhập ít nhất một trường ở tab Lấy hàng & Xuất khẩu.", "red");
			return;
		}
		c("shipment_field_save", {
			shipmentId: u.id,
			fields: e
		}), re("Đã lưu thông tin lấy hàng " + u.id);
	}, ae = () => {
		let e = O("tk", u.importInfo.declarationNo);
		if (!e) {
			o("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red");
			return;
		}
		let t = {};
		w.tkDate != null && (t.tk_date = w.tkDate.trim()), w.importDuty != null && (t.import_duty_amount = w.importDuty.trim()), w.importVat != null && (t.import_vat_amount = w.importVat.trim());
		let n = {
			tk_no: e,
			...ne({
				phan_luong: O("inspection", u.importInfo.inspection),
				arrival_date: O("arrivalDate", u.importInfo.arrivalDate ?? ""),
				free_time: O("freeTime", u.importInfo.freeTime == null ? "" : String(u.importInfo.freeTime)),
				truck_no: O("plateVN", u.importInfo.plateVN),
				seal_no: O("driverVN", u.importInfo.driverVN),
				delivery_date: O("schedule", u.importInfo.schedule)
			}),
			...t
		};
		c("shipment_field_save", {
			shipmentId: u.id,
			fields: n
		}), re("Đã lưu tờ khai " + e);
	}, A = () => {
		let e = c("delivery_confirm", {
			shipmentId: u.id,
			deliveredAt: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			receiverName: u.importInfo.receiver,
			receiverTitle: u.importInfo.receiverTitle ?? "",
			receiverPhone: u.importInfo.receiverPhone,
			deliveryLocation: u.importInfo.deliveryLocation || u.importInfo.deliveryAddr
		});
		m(!1), e ? o("Đã gửi xác nhận giao hàng " + u.id, "Backend ghi nhận + audit; PXK sẽ mở ở tab Chứng từ.", "green") : o("Không gửi được", "Component chưa kết nối backend.", "red");
	}, j = (0, _.useRef)(""), oe = () => {
		j.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, f(!0);
	}, se = () => {
		let e = Number(h.replace(/\D/g, ""));
		if (!e) {
			o("Chưa nhập số tiền", `Nhập số tiền ${k} rồi bấm Lưu — ví dụ 50.000.000.`, "red");
			return;
		}
		if (!c("payment_record", {
			shipmentId: u.id,
			amount: e,
			requestId: j.current,
			date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			note: v
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		f(!1), g(""), o("Đã gửi khoản thu " + B(e, k), "Ghi qua save_direct_shipment_payment với request identity — gửi lại cùng intent sẽ không nhân đôi.", "green");
	}, ce = (0, _.useRef)(""), le = (0, _.useRef)(""), ue = (e) => `${e}-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, M = () => {
		ce.current = ue("POBL");
	}, de = () => {
		le.current = ue("PPAY");
	}, fe = () => {
		let e = u.finance.partner;
		if (!e?.partnerId) {
			o("Chưa chọn đối tác", "Chưa có đối tác trong danh mục để ghi nhận phải trả.", "red");
			return;
		}
		let t = Number(b.replace(/\D/g, ""));
		if (!t) {
			o("Chưa nhập số tiền", `Nhập số tiền phải trả ${k} — ví dụ 57.000.000.`, "red");
			return;
		}
		if (ce.current || M(), !c("partner_payable_record", {
			shipmentId: u.id,
			partnerId: e.partnerId,
			amount: t,
			currency: k,
			requestId: ce.current,
			note: "Phải trả chi phí đối tác theo thực tế lô"
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		x(""), o("Đã gửi phải trả đối tác " + B(t, k), "Ghi qua canonical ledger (obligation) với request identity — gửi lại cùng intent sẽ không nhân đôi.", "green");
	}, pe = () => {
		let e = u.finance.partner;
		if (!e?.partnerId) {
			o("Chưa chọn đối tác", "Chưa có đối tác để thanh toán — ghi nhận phải trả trước.", "red");
			return;
		}
		let t = Number(b.replace(/\D/g, ""));
		if (!t) {
			o("Chưa nhập số tiền", `Nhập số tiền thanh toán ${k} — ví dụ 20.000.000.`, "red");
			return;
		}
		if (le.current || de(), !c("partner_payment_record", {
			shipmentId: u.id,
			partnerId: e.partnerId,
			amount: t,
			currency: k,
			requestId: le.current,
			date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			note: "Chuyển khoản thanh toán đối tác"
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		x(""), o("Đã gửi thanh toán đối tác " + B(t, k), "Ghi qua canonical ledger (transaction + allocation) — backend sẽ đọc lại còn phải trả.", "green");
	}, me = (e, t) => C((n) => ({
		...n,
		[e]: t
	})), he = () => {
		if (!S.name.trim()) {
			o("Thiếu tên dịch vụ", "Nhập tên dòng thực tế — ví dụ: Cước xe TQ.", "red");
			return;
		}
		if (!c("finance_actual_save", {
			shipmentId: u.id,
			line: {
				name: S.name.trim(),
				qty: S.qty,
				price: S.price,
				cost: S.cost,
				vat: S.vat
			}
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		o("Đã gửi dòng thực tế", "Ghi vào data['3.4'].details rồi core.logic tính lại phải thu / chi phí / lợi nhuận.", "green"), C({
			name: "",
			qty: "1",
			price: "",
			cost: "",
			vat: "8"
		});
	}, ge = () => {
		let e = O("pxkNo", u?.pxk.number ?? "").trim(), t = O("pxkDate", u?.pxk.date ?? "").trim();
		if (u) {
			if (!e || !t) {
				o("Chưa xuất được PXK", "core.docgen từ chối khi thiếu Số PXK hoặc Ngày PXK — nhập 2 ô ở tab Chứng từ rồi bấm lại.", "red");
				return;
			}
			c("pxk_generate", {
				shipmentId: u.id,
				pxkNo: e,
				pxkDate: t
			}) ? o("Đã gửi yêu cầu xuất PXK " + e, "core.docgen kiểm tra gate giao hàng, sinh file Office thật và lưu metadata chứng từ.", "blue") : o("Không gửi được", "Component chưa kết nối backend.", "red");
		}
	}, _e = () => {
		let e = ne({
			delivery_location: O("pxPlace", u.pxk.place || u.importInfo.deliveryAddr || ""),
			receiver_name: O("pxReceiver", u.pxk.receiver || u.importInfo.receiver || ""),
			receiver_title: O("pxRole", u.pxk.role ?? ""),
			delivery_date: O("pxDate", u.importInfo.schedule ?? "")
		});
		if (Object.keys(e).length === 0) {
			o("Chưa có gì để lưu", "Nhập ít nhất một trường người nhận / địa điểm / ngày giao.", "red");
			return;
		}
		c("shipment_field_save", {
			shipmentId: u.id,
			fields: e
		}), re("Đã lưu thông tin giao nhận " + u.id, ["pxkNo", "pxkDate"]);
	}, ve = () => {
		let e = u.pxk.document;
		if (!e || !e.downloadBase64) {
			o("File không còn trong phiên này", "Metadata PXK " + (u.pxk.number || u.id) + " vẫn còn trên backend; bytes chỉ được giữ trong phiên đã sinh. Bấm sinh lại để có file tải.", "amber");
			return;
		}
		qa(e.fileName || "PXK_" + (u.pxk.number || u.id) + ".xlsx", e.downloadBase64, e.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
	}, ye = (e) => /tờ khai|thông quan|xe giao|giao hàng/i.test(e) ? "nhap" : /lấy hàng|xe TQ|biển số|packing|container/i.test(e) ? "lay-hang" : /chứng từ|PXK|HDMB|PL$/i.test(e) ? "chung-tu" : "nhap", be = u.missingDocs.length;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("button", {
				onClick: () => l(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, F.jsx)(gr, { size: 17 }), " Quay lại"]
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
									be > 0 && /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "inline-flex items-center gap-1.5 text-[13px] font-bold bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1.5",
										children: [
											/* @__PURE__ */ (0, F.jsx)(Wr, { size: 15 }),
											" Thiếu ",
											be,
											" thông tin"
										]
									}),
									/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "ml-auto text-[12.5px] text-slate-400 flex items-center gap-1",
										children: [
											/* @__PURE__ */ (0, F.jsx)(Qr, { size: 14 }),
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
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Tuyến",
										value: u.route
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Cửa khẩu",
										value: u.borderVN
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Hợp đồng",
										value: /* @__PURE__ */ (0, F.jsx)(P, {
											to: "/hop-dong/" + u.contract,
											className: "text-[#1e5aa8] font-bold hover:underline",
											children: u.contract
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
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
						children: /* @__PURE__ */ (0, F.jsx)($a, {
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
						children: co.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => n({ tab: e.id }),
							className: z("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", r === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
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
						/* @__PURE__ */ (0, F.jsx)(Wr, { size: 18 }),
						" Đang thiếu ",
						u.missingDocs.length,
						" thông tin — bấm để bổ sung ngay:"
					]
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "grid gap-2 md:grid-cols-2",
					children: u.missingDocs.map((e) => /* @__PURE__ */ (0, F.jsx)(eo, {
						what: e,
						actionLabel: "Bổ sung ngay",
						onAction: () => {
							n({ tab: ye(e) }), setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({
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
							children: [/* @__PURE__ */ (0, F.jsx)(zi, {
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
										/* @__PURE__ */ (0, F.jsx)(Zi, {
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
							children: [/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Ngày lấy hàng (ETD)",
								required: !u.pickup.pickupTime,
								hint: "Backend lưu theo NGÀY; giờ hẹn trao đổi với nhà máy ngoài hệ thống.",
								error: O("pickupTime", u.pickup.pickupTime) ? void 0 : "Thiếu ngày lấy hàng — nhà máy cần báo trước 24h",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: O("pickupTime", u.pickup.pickupTime),
									onChange: (e) => D("pickupTime", e.target.value),
									placeholder: "VD: 10/09/2026",
									className: G(O("pickupTime", u.pickup.pickupTime) ? "ok" : "missing")
								})
							}), /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Loại / kích thước xe",
								hint: "Loại/kích thước xe lấy hàng TQ — VD: 17.5m · rộng 3m · tải ≤30t. Bỏ trống = chưa biết.",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									id: "fld-trucktype",
									value: O("truckType", u.pickup.truckType),
									onChange: (e) => D("truckType", e.target.value),
									placeholder: "VD: 17.5m · rộng 3m · tải ≤30t",
									className: G()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 pt-1",
							children: [/* @__PURE__ */ (0, F.jsx)(ba, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Xe Trung Quốc"]
						}),
						!u.pickup.plate && /* @__PURE__ */ (0, F.jsx)(eo, {
							what: "biển số xe TQ",
							where: "Chưa đặt được xe — bổ sung để nhà máy cho hàng lên xe",
							actionLabel: "Nhập xe ngay",
							onAction: () => document.getElementById("fld-plate")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Biển số xe",
									required: !u.pickup.plate,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-plate",
										value: O("plate", u.pickup.plate),
										onChange: (e) => D("plate", e.target.value),
										placeholder: "VD: 粤A·88T36",
										className: G(O("plate", u.pickup.plate) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Tài xế xe TQ",
									hint: "Lô hàng chưa có trường tài xế TQ — ghi ở sổ tay/điều phối, ô này không lưu.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.pickup.driver,
										readOnly: !0,
										placeholder: "Chưa có trường dữ liệu",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "SĐT tài xế TQ",
									hint: "Chưa có trường dữ liệu trong lô.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.pickup.driverPhone,
										readOnly: !0,
										placeholder: "Chưa có trường dữ liệu",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-2 gap-3",
									children: [/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Ngày dự kiến về kho",
										hint: "Là ngày ETA ở tab Nhập & Giao.",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: u.pickup.eta,
											readOnly: !0,
											className: G()
										})
									}), /* @__PURE__ */ (0, F.jsx)(W, {
										label: "Ngày thực tế",
										hint: "Chưa có trường dữ liệu trong lô.",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: u.pickup.ata,
											readOnly: !0,
											placeholder: "Chưa có trường dữ liệu",
											className: G()
										})
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(Xa, {
							onClick: ie,
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
									children: [/* @__PURE__ */ (0, F.jsx)(qi, {
										size: 19,
										className: "text-[#1e5aa8]"
									}), " Hàng hóa"]
								}),
								/* @__PURE__ */ (0, F.jsx)("div", {
									className: "grid grid-cols-2 md:grid-cols-3 gap-3",
									children: [
										["Số kiện / GW", V(u.cargo.qtyPkg)],
										["Số kiện", Ka(u.cargo.packs)],
										["CBM", Ka(u.cargo.cbm)],
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
								/* @__PURE__ */ (0, F.jsx)(to, {
									label: "Đơn vị khai",
									value: u.exportInfo.declarant
								}),
								/* @__PURE__ */ (0, F.jsx)(to, {
									label: "Ngày dự kiến / thực tế",
									value: /* @__PURE__ */ (0, F.jsxs)("span", { children: [
										u.exportInfo.eta || "—",
										" / ",
										u.exportInfo.ata || "chưa có"
									] })
								}),
								/* @__PURE__ */ (0, F.jsx)(to, {
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
										className: z("flex items-center gap-3 rounded-xl border-2 p-3", e.ok ? "border-emerald-200 bg-emerald-50/60" : "border-amber-300 bg-amber-50"),
										children: [
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: z("w-8 h-8 rounded-full grid place-items-center font-extrabold shrink-0", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
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
												children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Bổ sung"]
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
						!O("tk", u.importInfo.declarationNo) && /* @__PURE__ */ (0, F.jsx)(eo, {
							what: "số tờ khai nhập khẩu",
							where: "Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được",
							actionLabel: "Nhập số TK",
							onAction: () => document.getElementById("fld-tk")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Số tờ khai",
									required: !u.importInfo.declarationNo,
									error: O("tk", u.importInfo.declarationNo) ? void 0 : "Nhập 12 số tờ khai — VD: 105588421330",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-tk",
										value: O("tk", u.importInfo.declarationNo),
										onChange: (e) => D("tk", e.target.value),
										placeholder: "12 số tờ khai…",
										className: G(O("tk", u.importInfo.declarationNo) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Ngày đăng ký",
									hint: "Lưu vào ngày tờ khai (2.4.tk_date).",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-tkdate",
										value: O("tkDate", u.importInfo.regDate),
										onChange: (e) => D("tkDate", e.target.value),
										placeholder: "VD: 15/08/2026",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Thuế nhập khẩu (VND)",
									hint: "Số thực tế trên thông báo thuế/GNT — app không tự tính.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-duty",
										value: O("importDuty", u.importInfo.tax == null ? "" : String(u.importInfo.tax)),
										onChange: (e) => D("importDuty", e.target.value),
										inputMode: "decimal",
										placeholder: "Bỏ trống = chưa biết",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "VAT hàng nhập (VND)",
									hint: "Số thực tế trên thông báo thuế/GNT — app không tự tính.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-vat",
										value: O("importVat", u.importInfo.vat == null ? "" : String(u.importInfo.vat)),
										onChange: (e) => D("importVat", e.target.value),
										inputMode: "decimal",
										placeholder: "Bỏ trống = chưa biết",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Phân luồng / kiểm hóa",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: O("inspection", u.importInfo.inspection),
										onChange: (e) => D("inspection", e.target.value),
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Giấy phép chuyên ngành",
									hint: "Chỉ đọc — chưa có trường dữ liệu trong lô.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.importInfo.license,
										readOnly: !0,
										placeholder: "Chưa có trường dữ liệu",
										className: G()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(Xa, {
							onClick: ae,
							className: "w-full",
							children: "💾 LƯU TỜ KHAI & THUẾ"
						}),
						O("tk", u.importInfo.declarationNo) && /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13.5px] text-blue-900",
							children: [
								"✅ Đã có số TK ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: O("tk", u.importInfo.declarationNo) }),
								". Tiếp theo: nộp thuế rồi bấm “Thông quan” khi có kết quả phân luồng."
							]
						})
					]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(ba, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Xe Việt Nam & giao hàng"]
						}),
						(!u.importInfo.driverVN || !u.importInfo.plateVN) && !u.importInfo.delivered && /* @__PURE__ */ (0, F.jsx)(eo, {
							what: "xe VN + tài xế",
							where: "Chưa đặt xe — đặt trước giờ giao ít nhất 4 tiếng",
							actionLabel: "Đặt xe ngay",
							onAction: () => document.getElementById("fld-platevn")?.focus()
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Loại xe VN",
									hint: "Chỉ đọc — chưa có trường dữ liệu trong lô.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.importInfo.truckVN,
										readOnly: !0,
										placeholder: "Chưa có trường dữ liệu",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Biển số VN",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-platevn",
										value: O("plateVN", u.importInfo.plateVN),
										onChange: (e) => D("plateVN", e.target.value),
										placeholder: "VD: 29H-481.36",
										className: G(O("plateVN", u.importInfo.plateVN) ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Tài xế VN",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: O("driverVN", u.importInfo.driverVN),
										onChange: (e) => D("driverVN", e.target.value),
										placeholder: "Tên tài xế",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Lịch giao",
									hint: "Lưu vào ngày giao (2.7.delivery_date) — PXK cần ngày này.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-schedule",
										value: O("schedule", u.importInfo.schedule),
										onChange: (e) => D("schedule", e.target.value),
										placeholder: "VD: 12/09/2026",
										className: G()
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
									children: ["SANG XUẤT PHIẾU XUẤT KHO ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
								})
							]
						}) : /* @__PURE__ */ (0, F.jsx)(Za, {
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
								u.finance.quote.map((e) => /* @__PURE__ */ (0, F.jsx)(to, {
									label: e.label,
									value: /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "font-bold text-[16px]",
										children: [
											Va(e.amount, e.ccy),
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
												children: B(e.amount, e.ccy)
											})
										})]
									}), /* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[12.5px] text-slate-400 mt-0.5 text-right",
										children: [
											"Chi phí ",
											B(e.cost, e.ccy),
											e.qty == null ? "" : ` · SL ${Ka(e.qty)}`,
											e.vat == null ? "" : ` · VAT ${Ka(e.vat)}%`
										]
									})]
								}, `${e.label}-${t}`)),
								/* @__PURE__ */ (0, F.jsx)(to, {
									label: "Doanh thu thực tế (chưa VAT)",
									value: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-bold",
										children: B(u.finance.receivableNet, k)
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(to, {
									label: "Chi phí thực tế",
									value: /* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-bold",
										children: B(u.finance.payable, k)
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
												className: z("font-extrabold text-[17px]", u.finance.profit == null ? "text-slate-400" : u.finance.profit < 0 ? "text-red-700" : "text-emerald-700"),
												children: B(u.finance.profit, k)
											})] }), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Biên lợi nhuận"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: z("font-extrabold text-[17px]", u.finance.profitMargin == null ? "text-slate-400" : u.finance.profitMargin < 0 ? "text-red-700" : "text-emerald-700"),
												children: Wa(u.finance.profitMargin)
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
												/* @__PURE__ */ (0, F.jsx)(W, {
													label: "Dịch vụ",
													required: !0,
													error: S.name.trim() ? void 0 : "Nhập tên dịch vụ",
													children: /* @__PURE__ */ (0, F.jsx)("input", {
														value: S.name,
														onChange: (e) => me("name", e.target.value),
														placeholder: "VD: Cước xe TQ Đông Bằng → Hữu Nghị",
														className: G(S.name.trim() ? "ok" : "missing")
													})
												}),
												/* @__PURE__ */ (0, F.jsxs)("div", {
													className: "grid grid-cols-2 gap-2.5",
													children: [/* @__PURE__ */ (0, F.jsx)(W, {
														label: `Giá bán (${k})`,
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: S.price,
															onChange: (e) => me("price", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 62000000",
															className: G()
														})
													}), /* @__PURE__ */ (0, F.jsx)(W, {
														label: `Chi phí (${k})`,
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: S.cost,
															onChange: (e) => me("cost", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 57000000",
															className: G()
														})
													})]
												}),
												/* @__PURE__ */ (0, F.jsxs)("div", {
													className: "grid grid-cols-2 gap-2.5",
													children: [/* @__PURE__ */ (0, F.jsx)(W, {
														label: "Số lượng",
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: S.qty,
															onChange: (e) => me("qty", e.target.value),
															inputMode: "numeric",
															placeholder: "VD: 1",
															className: G()
														})
													}), /* @__PURE__ */ (0, F.jsx)(W, {
														label: "VAT %",
														hint: "Bỏ trống = chưa xác định",
														children: /* @__PURE__ */ (0, F.jsx)("input", {
															value: S.vat,
															onChange: (e) => me("vat", e.target.value),
															inputMode: "decimal",
															placeholder: "VD: 8",
															className: G()
														})
													})]
												})
											]
										}),
										/* @__PURE__ */ (0, F.jsx)(Xa, {
											onClick: he,
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
										/* @__PURE__ */ (0, F.jsx)(Oa, {
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
												children: Ua(u.finance.receivable, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-emerald-700 font-semibold",
												children: "Đã thu"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-emerald-700",
												children: Ua(u.finance.received, k)
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-red-50 border border-red-200 p-3",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[12px] text-red-600 font-semibold",
												children: "Còn phải thu"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-red-700",
												children: Ua(u.finance.outstanding, k)
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Phải thu = doanh thu thực tế + VAT đầu ra. Còn phải thu = phải thu − đã thu, do backend tính."
								}),
								/* @__PURE__ */ (0, F.jsx)("button", {
									onClick: oe,
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
								(() => {
									let e = u.finance.partner, t = e?.partnerId ?? "", n = e?.partnerName, r = e?.suggested === !0;
									return /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "flex flex-wrap items-center gap-2 mb-2",
										children: [/* @__PURE__ */ (0, F.jsx)("span", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Đối tác:"
										}), n ? /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "inline-flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0f2a4a]",
											children: [
												/* @__PURE__ */ (0, F.jsx)(Pr, {
													size: 15,
													className: "text-[#1e5aa8]"
												}),
												" ",
												n,
												/* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-[11.5px] font-bold text-slate-400",
													children: t
												}),
												r && /* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5",
													children: "đề xuất từ danh mục"
												})
											]
										}) : /* @__PURE__ */ (0, F.jsx)("span", {
											className: "text-[13.5px] font-bold text-slate-400",
											children: "—"
										})]
									}), /* @__PURE__ */ (0, F.jsxs)("div", {
										className: "grid grid-cols-3 gap-2 text-center",
										children: [
											/* @__PURE__ */ (0, F.jsxs)("div", {
												className: "rounded-xl bg-slate-50 border p-3",
												children: [/* @__PURE__ */ (0, F.jsx)("p", {
													className: "text-[12px] text-slate-500 font-semibold",
													children: "Phải trả"
												}), /* @__PURE__ */ (0, F.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px]",
													children: Ua(e?.payable ?? null, k)
												})]
											}),
											/* @__PURE__ */ (0, F.jsxs)("div", {
												className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
												children: [/* @__PURE__ */ (0, F.jsx)("p", {
													className: "text-[12px] text-blue-700 font-semibold",
													children: "Đã trả"
												}), /* @__PURE__ */ (0, F.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px] text-blue-700",
													children: Ua(e?.paid ?? null, k)
												})]
											}),
											/* @__PURE__ */ (0, F.jsxs)("div", {
												className: "rounded-xl bg-amber-50 border border-amber-200 p-3",
												children: [/* @__PURE__ */ (0, F.jsx)("p", {
													className: "text-[12px] text-amber-700 font-semibold",
													children: "Còn phải trả"
												}), /* @__PURE__ */ (0, F.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px] text-amber-800",
													children: Ua(e?.remaining ?? null, k)
												})]
											})
										]
									})] });
								})(),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: [
										"Phải trả / đã trả / còn lại đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ) theo lô này. Chưa có sổ ⇒ “—”, không suy ra 0. Đơn vị: ",
										k,
										" — không quy đổi."
									]
								}),
								(u.finance.partner?.payments?.length ?? 0) > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5",
										children: "Lịch sử trả đối tác"
									}), /* @__PURE__ */ (0, F.jsx)("div", {
										className: "space-y-1.5",
										children: u.finance.partner.payments.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
											className: "flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-2.5",
											children: [
												/* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-[12px] font-bold text-slate-400 w-[80px]",
													children: e.date || "—"
												}),
												/* @__PURE__ */ (0, F.jsxs)("span", {
													className: "flex-1 min-w-[140px] text-[12.5px] text-slate-600",
													children: [e.note || e.kind, e.requestId ? ` · ${e.requestId}` : ""]
												}),
												/* @__PURE__ */ (0, F.jsxs)("span", {
													className: "font-extrabold text-[14.5px]",
													children: [
														Va(e.amount, e.ccy),
														" ",
														/* @__PURE__ */ (0, F.jsx)("span", {
															className: "text-[11px] text-slate-400",
															children: e.ccy
														})
													]
												})
											]
										}, e.id || t))
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3 rounded-xl border border-slate-200 p-3",
									children: [
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[13px] font-extrabold text-[#0f2a4a] mb-2",
											children: "Ghi nhận phải trả & thanh toán đối tác"
										}),
										/* @__PURE__ */ (0, F.jsx)(W, {
											label: `Số tiền (${k})`,
											hint: "Ví dụ: 20.000.000 — để trống là UNKNOWN, không tự thành 0",
											children: /* @__PURE__ */ (0, F.jsx)("input", {
												value: b,
												onChange: (e) => {
													x(e.target.value), M(), de();
												},
												inputMode: "numeric",
												placeholder: "VD: 20000000",
												className: G()
											})
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2.5",
											children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
												onClick: fe,
												className: "min-h-[48px]",
												children: "📌 GHI NHẬN PHẢI TRẢ"
											}), /* @__PURE__ */ (0, F.jsx)(Xa, {
												onClick: pe,
												className: "min-h-[48px]",
												children: "💸 TRẢ ĐỐI TÁC"
											})]
										})
									]
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
											Va(e.amount, e.ccy),
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
							children: [/* @__PURE__ */ (0, F.jsx)(bi, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Hợp đồng liên kết"]
						}),
						te ? /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl border-2 border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex flex-wrap items-center gap-2",
									children: [/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: te.id
									}), /* @__PURE__ */ (0, F.jsx)(H, {
										tone: te.statusTone,
										size: "sm",
										children: te.status
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[14px] text-slate-600 mt-1",
									children: [
										te.companyLegal,
										" · Giá trị ",
										Ha(te.value ?? u.finance.receivable)
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-2 gap-2 mt-3",
									children: [/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/hop-dong/" + te.id,
										className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]",
										children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 16 }), " MỞ HỢP ĐỒNG"]
									}), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => {
											n({ tab: "chung-tu" }), o("Chứng từ " + te.id, "Chứng từ được sinh bởi core.docgen (Office thật) ở tab Chứng từ & PXK.", "blue");
										},
										className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]",
										children: [/* @__PURE__ */ (0, F.jsx)(gi, { size: 16 }), " MỞ CHỨNG TỪ"]
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
								children: "Chứng từ lô hàng — hiện trạng & bổ sung"
							}), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "space-y-2",
								children: u.docs.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5",
									children: [
										/* @__PURE__ */ (0, F.jsx)("span", {
											className: z("w-7 h-7 rounded-full grid place-items-center text-[13px] font-extrabold", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
											children: e.ok ? "✓" : "!"
										}),
										/* @__PURE__ */ (0, F.jsxs)("span", {
											className: "flex-1 font-semibold text-[14px]",
											children: [
												e.name,
												" — ",
												e.ok ? /* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-emerald-700",
													children: "Đã đủ"
												}) : /* @__PURE__ */ (0, F.jsx)("span", {
													className: "text-amber-800",
													children: "Thiếu"
												})
											]
										}),
										!e.ok && /* @__PURE__ */ (0, F.jsxs)("button", {
											onClick: () => {
												n({ tab: ye(e.name) }), o("Mở tab bổ sung", "Đi tới ô nhập liệu thật cho " + e.name + ".", "blue");
											},
											className: "btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13px] font-bold px-3 min-h-[44px]",
											children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Bổ sung"]
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
						!u.importInfo.delivered && /* @__PURE__ */ (0, F.jsx)(eo, {
							what: "xác nhận đã giao hàng",
							where: "Phải giao xong mới được xuất PXK",
							actionLabel: "Sang xác nhận giao",
							onAction: () => n({ tab: "nhap" })
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Số PXK",
									required: !u.pxk.number,
									hint: "Số pháp lý của phiếu — backend không tự đặt.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxkno",
										value: O("pxkNo", u.pxk.number ?? ""),
										onChange: (e) => D("pxkNo", e.target.value),
										placeholder: "VD: PXK-2026-0308",
										className: G(O("pxkNo", u.pxk.number ?? "") ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Ngày PXK",
									required: !u.pxk.date,
									hint: "DD/MM/YYYY hoặc YYYY-MM-DD.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxkdate",
										value: O("pxkDate", u.pxk.date ?? ""),
										onChange: (e) => D("pxkDate", e.target.value),
										placeholder: "VD: 11/09/2026",
										className: G(O("pxkDate", u.pxk.date ?? "") ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Địa điểm nhận",
									required: !u.pxk.place,
									hint: "Lưu vào 2.7.delivery_location — PXK bị chặn nếu thiếu.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxplace",
										value: O("pxPlace", u.pxk.place || u.importInfo.deliveryAddr || ""),
										onChange: (e) => D("pxPlace", e.target.value),
										placeholder: "Kho / địa chỉ nhận thực tế",
										className: G(O("pxPlace", u.pxk.place || u.importInfo.deliveryAddr || "") ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Người nhận",
									required: !u.pxk.receiver,
									hint: "Lưu vào 2.7.receiver_name.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxreceiver",
										value: O("pxReceiver", u.pxk.receiver || u.importInfo.receiver || ""),
										onChange: (e) => D("pxReceiver", e.target.value),
										placeholder: "Tên người nhận",
										className: G(O("pxReceiver", u.pxk.receiver || u.importInfo.receiver || "") ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Chức vụ người nhận",
									required: !u.pxk.role,
									hint: "Lưu vào 2.7.receiver_title.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxrole",
										value: O("pxRole", u.pxk.role ?? ""),
										onChange: (e) => D("pxRole", e.target.value),
										placeholder: "Theo giấy giới thiệu",
										className: G(O("pxRole", u.pxk.role ?? "") ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Ngày giao",
									hint: "Lưu vào 2.7.delivery_date — PXK cần ngày này.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										id: "fld-pxdate",
										value: O("pxDate", u.importInfo.schedule ?? ""),
										onChange: (e) => D("pxDate", e.target.value),
										placeholder: "VD: 12/09/2026",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Nguồn (HDMB/PL)",
									hint: "Từ hợp đồng đã liên kết với lô — liên kết ở màn Hợp đồng.",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: u.pxk.source || u.contract,
										readOnly: !0,
										placeholder: "Chưa liên kết chứng từ nguồn",
										className: G()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(Xa, {
							onClick: _e,
							className: "w-full mt-3",
							children: "💾 LƯU THÔNG TIN GIAO NHẬN"
						}),
						(u.pxk.missingDeliveryFacts ?? []).length > 0 && /* @__PURE__ */ (0, F.jsx)(eo, {
							what: (u.pxk.missingDeliveryFacts ?? []).join(" · "),
							where: "core.docgen chặn PXK đến khi đủ thông tin giao nhận",
							actionLabel: "Nhập ở trên",
							onAction: () => document.getElementById("fld-pxplace")?.focus()
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
							children: [
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "font-extrabold text-emerald-800",
									children: ["✅ ĐÃ XUẤT ", u.pxk.number]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[13.5px] text-emerald-700 mt-0.5",
									children: [
										u.pxk.document?.fileName || "PXK",
										" · bản R",
										u.pxk.document?.revision ?? 1,
										" · ",
										u.pxk.document?.status || "GENERATED",
										u.pxk.document?.generatedBy ? " · " + u.pxk.document.generatedBy : ""
									]
								}),
								u.pxk.document?.downloadAvailable ? /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: ve,
									className: "btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]",
									children: [
										/* @__PURE__ */ (0, F.jsx)(oi, { size: 17 }),
										" TẢI ",
										u.pxk.document?.fileName || "PXK"
									]
								}) : /* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] text-emerald-800 mt-2",
									children: "File sinh ở phiên trước: metadata còn trên backend, bytes chỉ giữ trong phiên đã sinh — bấm “SINH BẢN MỚI” để có file tải."
								}),
								/* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: ge,
									className: "btn-press touch-target mt-2 ml-2 inline-flex items-center gap-1.5 rounded-xl border-2 border-emerald-600 text-emerald-800 font-bold px-5 min-h-[48px]",
									children: [/* @__PURE__ */ (0, F.jsx)(gi, { size: 17 }), " SINH BẢN MỚI (R+1)"]
								})
							]
						}) : /* @__PURE__ */ (0, F.jsx)(Za, {
							onClick: ge,
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
							/* @__PURE__ */ (0, F.jsx)("span", { className: z("absolute -left-6 top-1 w-4 h-4 rounded-full border-[3px] border-white shadow", e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : e.tone === "red" ? "bg-red-500" : "bg-blue-500") }),
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
						onClick: ge,
						className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]",
						children: "🖨 XUẤT PHIẾU XUẤT KHO"
					}),
					r === "tai-chinh" && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: oe,
						className: "btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
						children: "＋ GHI NHẬN THANH TOÁN"
					}),
					(r === "lay-hang" || r === "lich-su") && /* @__PURE__ */ (0, F.jsx)("button", {
						onClick: ie,
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
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => m(!1),
								children: "Chưa, để sau"
							}), /* @__PURE__ */ (0, F.jsx)(Za, {
								onClick: A,
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
								children: B(u.finance.outstanding, k)
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Loại khoản",
								children: /* @__PURE__ */ (0, F.jsxs)("select", {
									value: v,
									onChange: (e) => y(e.target.value),
									className: G(),
									children: [
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tiền khách" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tạm ứng" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu nốt công nợ" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Trả đối tác" })
									]
								})
							}), /* @__PURE__ */ (0, F.jsx)(W, {
								label: `Số tiền (${k})`,
								required: !0,
								error: h ? void 0 : "Nhập số tiền — VD: 150000000",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: h,
									onChange: (e) => g(e.target.value),
									inputMode: "numeric",
									placeholder: "VD: 150000000",
									className: G(h ? "ok" : "missing")
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
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => f(!1),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(Za, {
								onClick: se,
								children: "💾 LƯU KHOẢN THU"
							})]
						})
					]
				})]
			}),
			ee > 0 && /* @__PURE__ */ (0, F.jsx)("span", { className: "hidden" })
		]
	});
}
//#endregion
//#region src/pages/CreateShipment.tsx
function uo() {
	let { customers: e, quotes: t, contracts: n, dispatch: r, toast: i } = Zn(), a = Ct(), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)(""), [u, d] = (0, _.useState)(""), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)("Truck"), [g, v] = (0, _.useState)("DAP"), [y, b] = (0, _.useState)(""), [x, S] = (0, _.useState)(""), [C, w] = (0, _.useState)(""), [T, ee] = (0, _.useState)(""), [E, D] = (0, _.useState)(""), O = (0, _.useMemo)(() => t.filter((e) => (e.status || "").toLowerCase().includes("accept") || (e.status || "").toLowerCase().includes("chốt")), [t]), te = t.find((e) => e.id === o) ?? null, k = (r) => {
		s(r);
		let a = t.find((e) => e.id === r);
		if (!a) return;
		let o = e.find((e) => e.id === a.customerId) ?? e.find((e) => e.name === a.customer);
		o && d(o.id);
		let c = a.customerId ? n.filter((e) => e.customerId === a.customerId) : [];
		if (c.length === 1) {
			p(c[0].id), i("Đã nạp báo giá " + r, "Khách hàng + hợp đồng " + c[0].id + " đã điền sẵn từ báo giá đã chốt.", "blue");
			return;
		}
		if (c.length > 1) {
			p(""), i("Đã nạp báo giá " + r, `Khách ${a.customer} có ${c.length} hợp đồng — chọn đúng hợp đồng ở ô “Hợp đồng liên kết”.`, "amber");
			return;
		}
		i("Đã nạp báo giá " + r, "Giá trị và khách hàng đã được điền sẵn từ báo giá đã chốt.", "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1000px]",
		children: [/* @__PURE__ */ (0, F.jsxs)(P, {
			to: "/lo-hang",
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, F.jsx)(gr, { size: 17 }), " Về danh sách lô"]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
			children: [/* @__PURE__ */ (0, F.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }), /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "p-4 md:p-6",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						title: "Tạo Lô Hàng Mới",
						sub: "Bắt đầu từ báo giá đã chốt để tự điền, rồi chỉ bổ sung phần còn thiếu. Ghi bằng writer hiện có của Logistics."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-2xl bg-blue-50 border border-blue-200 p-4 mb-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-extrabold text-[15px] text-blue-900 flex items-center gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)(fa, { size: 17 }), " 1 · Chọn báo giá đã chốt (không bắt buộc)"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3",
								children: [O.length === 0 && /* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[14px] text-blue-800",
									children: "Chưa có báo giá đã chốt trong dữ liệu hiện tại — có thể nhập tay bên dưới."
								}), O.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => k(e.id),
									className: z("touch-target text-left rounded-xl border-2 bg-white p-3.5 lift", o === e.id ? "border-[#1e5aa8]" : "border-slate-200"),
									children: [
										/* @__PURE__ */ (0, F.jsxs)("p", {
											className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-1.5",
											children: [
												/* @__PURE__ */ (0, F.jsx)(mi, {
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
												Va(e.total),
												" ",
												e.currency ?? "VND"
											]
										})
									]
								}, e.id))]
							}),
							te && /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13.5px] text-blue-900 mt-3",
								children: [
									"Đã chọn ",
									/* @__PURE__ */ (0, F.jsx)("b", { children: te.id }),
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
								children: [/* @__PURE__ */ (0, F.jsx)(qi, { size: 17 }), " 2 · Thông tin lô"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
								children: [
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Mã lô (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: c,
											onChange: (e) => l(e.target.value.toUpperCase()),
											placeholder: "LO-0470",
											className: G(c.trim() ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Khách hàng (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, F.jsxs)("select", {
											value: u,
											onChange: (e) => d(e.target.value),
											className: G(u ? "ok" : "missing"),
											children: [/* @__PURE__ */ (0, F.jsx)("option", {
												value: "",
												children: "-- Chọn khách hàng --"
											}), e.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
												value: e.id,
												children: [
													e.name,
													e.mst ? ` · MST ${e.mst}` : "",
													" · ",
													e.id
												]
											}, e.id))]
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Hợp đồng liên kết",
										hint: "PXK/chứng từ của lô lấy nguồn từ hợp đồng này; sau khi tạo lô thì không đổi được ở màn lô.",
										children: /* @__PURE__ */ (0, F.jsxs)("select", {
											value: f,
											onChange: (e) => p(e.target.value),
											className: G(),
											children: [/* @__PURE__ */ (0, F.jsx)("option", {
												value: "",
												children: "-- Chưa liên kết --"
											}), n.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
												value: e.id,
												children: [
													e.id,
													" · ",
													e.client || "chưa rõ khách",
													e.customerId ? ` · ${e.customerId}` : ""
												]
											}, e.id))]
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Mode / Incoterm",
										children: /* @__PURE__ */ (0, F.jsxs)("div", {
											className: "flex gap-2",
											children: [/* @__PURE__ */ (0, F.jsx)("select", {
												value: m,
												onChange: (e) => h(e.target.value),
												className: G(),
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
												className: G(),
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
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Nơi lấy hàng (POL)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: y,
											onChange: (e) => b(e.target.value),
											placeholder: "Bằng Tường (Quảng Tây)",
											className: G()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Điểm đến (POD)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: x,
											onChange: (e) => S(e.target.value),
											placeholder: "Hữu Nghị (Lạng Sơn)",
											className: G()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "Ngày khởi hành (ETD)",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: C,
											onChange: (e) => w(e.target.value),
											placeholder: "DD/MM/YYYY",
											className: G()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)(W, {
										label: "SĐT người nhận",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: E,
											onChange: (e) => D(e.target.value),
											placeholder: "0912…",
											className: G()
										})
									}),
									/* @__PURE__ */ (0, F.jsx)("div", {
										className: "md:col-span-2",
										children: /* @__PURE__ */ (0, F.jsx)(W, {
											label: "Địa chỉ giao hàng",
											children: /* @__PURE__ */ (0, F.jsx)("input", {
												value: T,
												onChange: (e) => ee(e.target.value),
												placeholder: "Kho khách — KCN…",
												className: G()
											})
										})
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-col sm:flex-row gap-2.5 mt-4",
								children: [/* @__PURE__ */ (0, F.jsxs)(Xa, {
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
											customerId: e.find((e) => e.id === u)?.id ?? "",
											customer: e.find((e) => e.id === u)?.name ?? "",
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
												phone_receiver: E.trim()
											}
										}) ? (i("Đã gửi yêu cầu tạo " + c.trim().toUpperCase(), "Backend validate + ghi + audit. Mã trùng sẽ bị từ chối.", "green"), a("/lo-hang")) : i("Không gửi được", "Component chưa kết nối backend.", "red");
									},
									className: "flex-1",
									children: ["TẠO LÔ HÀNG ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
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
function fo() {
	let { shipments: e } = Zn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(""), a = (0, _.useMemo)(() => e.filter((e) => !r || (e.id + e.customer + (e.transport?.containerNo ?? "")).toLowerCase().includes(r.toLowerCase())), [e, r]), o = e.find((e) => e.id === t) ?? a[0] ?? null, s = o?.tracking ?? null;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
			children: [/* @__PURE__ */ (0, F.jsx)(U, {
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
						className: z("touch-target w-full text-left p-3.5 hover:bg-slate-50", o?.id === e.id ? "bg-blue-50" : ""),
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ya, { tone: e.statusTone }),
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
								/* @__PURE__ */ (0, F.jsx)(ba, {
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
										children: ["Mở trang hãng ", /* @__PURE__ */ (0, F.jsx)(ui, { size: 15 })]
									}) : /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[15px] text-slate-400 mt-0.5",
										children: "—"
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 flex items-start gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(zi, {
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
							children: [/* @__PURE__ */ (0, F.jsx)(Gi, {
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
									children: [/* @__PURE__ */ (0, F.jsx)("span", { className: z("absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white", e.done ? e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500" : "bg-slate-300") }), /* @__PURE__ */ (0, F.jsxs)("div", {
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
//#region src/pages/Receivables.tsx
function po() {
	let { receivables: e, dispatch: t, toast: n } = Zn(), [r, i] = (0, _.useState)(""), [a, o] = (0, _.useState)(!1), [s, c] = (0, _.useState)(!1), [l, u] = (0, _.useState)("ALL"), [d, f] = (0, _.useState)("ALL"), [p, m] = (0, _.useState)("ALL"), [h, g] = (0, _.useState)("ALL"), [v, y] = (0, _.useState)(null), [b, x] = (0, _.useState)(""), [S, C] = (0, _.useState)("Thu tiền khách"), w = (0, _.useRef)(""), T = e.rows ?? [], ee = e.totals ?? {}, E = ["ALL", ...Array.from(new Set(T.map((e) => e.currency)))], D = ["ALL", ...Array.from(new Set(T.map((e) => e.sale).filter((e) => e)))], O = ["ALL", ...Array.from(new Set(T.map((e) => e.support).filter((e) => e)))], te = ["ALL", ...Array.from(new Set(T.map((e) => e.status)))], k = (0, _.useMemo)(() => {
		let e = r.trim().toLowerCase();
		return T.filter((t) => !(s && !(t.outstanding != null && t.outstanding > 0) || l !== "ALL" && t.currency !== l || d !== "ALL" && (t.sale || "") !== d || p !== "ALL" && (t.support || "") !== p || h !== "ALL" && t.status !== h || e && !(t.id + " " + t.customer + " " + (t.sale || "") + " " + (t.support || "")).toLowerCase().includes(e))).sort((e, t) => (t.outstanding ?? -1) - (e.outstanding ?? -1));
	}, [
		T,
		r,
		s,
		l,
		d,
		p,
		h
	]), ne = (e) => {
		w.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, x(""), C("Thu tiền khách"), y(e);
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Oa, {
							size: 20,
							className: "text-emerald-600"
						}),
						title: "Thu tiền khách · Phải thu",
						sub: "Toàn bộ phải thu khách hàng theo lô — đọc từ sổ tài chính thật (core.logic). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [Object.keys(ee).length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có lô nào chốt dòng thực tế — phải thu đang ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
								", không phải 0."
							]
						}), Object.entries(ee).map(([e, t]) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 mb-2",
								children: [/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500",
									children: ["Tổng phải thu · ", e]
								}), /* @__PURE__ */ (0, F.jsx)("span", {
									className: "text-[11px] text-slate-400",
									children: "không quy đổi sang đồng tiền khác"
								})]
							}), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 text-center",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-white border p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Phải thu"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]",
											children: B(t.receivable, e)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-emerald-700 font-semibold",
											children: "Đã thu"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-emerald-700",
											children: B(t.received, e)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-red-50 border border-red-200 p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-red-600 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-red-700",
											children: B(t.outstanding, e)
										})]
									})
								]
							})]
						}, e))]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex gap-2 mt-4",
						children: [/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: r,
								onChange: (e) => i(e.target.value),
								placeholder: "Tìm mã lô (LO-0306), khách (An Phát), Sale, Support…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => o((e) => !e),
							className: z("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", a ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, F.jsx)(ua, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					a && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => c((e) => !e),
								className: z("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", s ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600"),
								children: [/* @__PURE__ */ (0, F.jsx)(Wr, { size: 16 }), " Chỉ lô còn phải thu"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đồng tiền:"
								}), E.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => u(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", l === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Sale:"
								}), D.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => f(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", d === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : V(e)
								}, e))]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Support:"
								}), O.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => m(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", p === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : V(e)
								}, e))]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Trạng thái:"
								}), te.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => g(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", h === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [k.length, " lô"]
							}),
							" · Ưu tiên theo còn phải thu thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật."
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
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Lô" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Phải thu" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Đã thu" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Còn lại" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Đồng tiền" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Sale · Support" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: k.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(P, {
									to: "/lo-hang/" + e.id + "?tab=tai-chinh",
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: V(e.customer)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold",
									children: B(e.receivable, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "text-emerald-700 font-semibold",
									children: B(e.received, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: z("font-extrabold", !Ba(e.outstanding) && (e.outstanding ?? 0) > 0 ? "text-red-700" : "text-slate-500"),
									children: B(e.outstanding, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("span", {
									className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
									children: e.currency
								}) }),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Sale: ", /* @__PURE__ */ (0, F.jsx)("b", { children: V(e.sale) })]
									}), /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["SP: ", /* @__PURE__ */ (0, F.jsx)("b", { children: V(e.support) })]
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: e.statusTone,
									size: "sm",
									children: V(e.status)
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/lo-hang/" + e.id + "?tab=tai-chinh",
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }), " Mở lô"]
									}), (e.outstanding ?? 0) > 0 && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => ne(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-emerald-600 text-white text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Oa, { size: 15 }), " Thu tiền"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [k.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ya, { tone: e.statusTone }),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: e.statusTone,
										size: "sm",
										children: V(e.status)
									}),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
										children: e.currency
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: V(e.customer)
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 mt-2.5 text-center",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-slate-50 border p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-slate-500 font-semibold",
											children: "Phải thu"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px]",
											children: B(e.receivable, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-emerald-50 border border-emerald-200 p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-emerald-700 font-semibold",
											children: "Đã thu"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px] text-emerald-700",
											children: B(e.received, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-red-50 border border-red-200 p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-red-600 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px] text-red-700",
											children: B(e.outstanding, e.currency)
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-2",
								children: [
									"Sale ",
									V(e.sale),
									" · SP ",
									V(e.support)
								]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/lo-hang/" + e.id + "?tab=tai-chinh",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 17 }), " MỞ LÔ"]
						}), (e.outstanding ?? 0) > 0 ? /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => ne(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-emerald-600 text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Oa, { size: 17 }), " THU TIỀN"]
						}) : /* @__PURE__ */ (0, F.jsx)("span", {
							className: "flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]",
							children: "Đã thu đủ"
						})]
					})]
				}, e.id)), k.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy lô nào"
					}), /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Thử từ khóa khác hoặc bỏ bớt bộ lọc."
					})]
				})]
			}),
			v && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => y(null)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Ghi nhận khoản thu — ", v.id]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[13.5px] text-slate-500 mt-1",
							children: [
								"Khách ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: V(v.customer) }),
								" · Còn phải thu: ",
								/* @__PURE__ */ (0, F.jsx)("b", {
									className: "text-red-700",
									children: B(v.outstanding, v.currency)
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Loại khoản",
								children: /* @__PURE__ */ (0, F.jsxs)("select", {
									value: S,
									onChange: (e) => C(e.target.value),
									className: G(),
									children: [
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tiền khách" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu tạm ứng" }),
										/* @__PURE__ */ (0, F.jsx)("option", { children: "Thu nốt công nợ" })
									]
								})
							}), /* @__PURE__ */ (0, F.jsx)(W, {
								label: `Số tiền (${v.currency})`,
								required: !0,
								error: b ? void 0 : "Nhập số tiền — VD: 150000000",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: b,
									onChange: (e) => x(e.target.value),
									inputMode: "numeric",
									placeholder: "VD: 150000000",
									className: G(b ? "ok" : "missing")
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: [
								"Ghi theo đồng tiền của lô (",
								v.currency,
								") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai."
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => y(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(Za, {
								onClick: () => {
									if (!v) return;
									let e = Number(b.replace(/\D/g, ""));
									if (!e) {
										n("Chưa nhập số tiền", `Nhập số tiền ${v.currency} rồi bấm Lưu — ví dụ 50.000.000.`, "red");
										return;
									}
									if (!t("payment_record", {
										shipmentId: v.id,
										amount: e,
										requestId: w.current,
										date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
										note: S
									})) {
										n("Không gửi được", "Component chưa kết nối backend.", "red");
										return;
									}
									n("Đã gửi khoản thu " + B(e, v.currency), "Ghi qua save_direct_shipment_payment — gửi lại cùng intent không nhân đôi.", "green"), y(null), x("");
								},
								children: "💾 LƯU KHOẢN THU"
							})]
						})
					]
				})]
			}),
			k.length > 0 && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "md:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: /* @__PURE__ */ (0, F.jsxs)(P, {
					to: "/lo-hang",
					className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px] flex items-center justify-center",
					children: ["XEM LÔ HÀNG ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
				})
			})
		]
	});
}
//#endregion
//#region src/pages/PartnerPayables.tsx
var mo = (e) => e === "CONFIRMED" ? "blue" : e === "REVIEW_REQUIRED" ? "amber" : "gray";
function ho() {
	let { payables: e, dispatch: t, toast: n } = Zn(), [r, i] = (0, _.useState)(""), [a, o] = (0, _.useState)(!1), [s, c] = (0, _.useState)(!1), [l, u] = (0, _.useState)("ALL"), [d, f] = (0, _.useState)("ALL"), [p, m] = (0, _.useState)("ALL"), [h, g] = (0, _.useState)(null), [v, y] = (0, _.useState)(""), b = (0, _.useRef)(""), x = e.rows ?? [], S = e.totals ?? {}, C = ["ALL", ...Array.from(new Set(x.map((e) => e.currency)))], w = ["ALL", ...Array.from(new Set(x.map((e) => e.partnerId)))], T = ["ALL", ...Array.from(new Set(x.map((e) => e.status)))], ee = (e) => x.find((t) => t.partnerId === e)?.partnerName ?? e, E = (0, _.useMemo)(() => {
		let e = r.trim().toLowerCase();
		return x.filter((t) => !(s && !(t.remaining != null && t.remaining > 0) || l !== "ALL" && t.currency !== l || d !== "ALL" && t.partnerId !== d || p !== "ALL" && t.status !== p || e && !(t.shipmentId + " " + t.partnerName + " " + t.partnerId).toLowerCase().includes(e))).sort((e, t) => (t.remaining ?? -1) - (e.remaining ?? -1));
	}, [
		x,
		r,
		s,
		l,
		d,
		p
	]), D = (e) => {
		b.current = `PPAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, y(""), g(e);
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Oa, {
							size: 20,
							className: "text-[#1e5aa8]"
						}),
						title: "Thanh toán đối tác · Phải trả",
						sub: "Toàn bộ phải trả đối tác theo lô — đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [Object.keys(S).length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có khoản phải trả đối tác nào được ghi nhận — phải trả đang ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
								", không phải 0."
							]
						}), Object.entries(S).map(([e, t]) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 mb-2",
								children: [/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500",
									children: ["Tổng phải trả · ", e]
								}), /* @__PURE__ */ (0, F.jsx)("span", {
									className: "text-[11px] text-slate-400",
									children: "không quy đổi sang đồng tiền khác"
								})]
							}), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 text-center",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-white border p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Phải trả"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]",
											children: B(t.payable, e)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-blue-700 font-semibold",
											children: "Đã trả"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-blue-700",
											children: B(t.paid, e)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-amber-50 border border-amber-200 p-3",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-amber-700 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-amber-800",
											children: B(t.remaining, e)
										})]
									})
								]
							})]
						}, e))]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex gap-2 mt-4",
						children: [/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, F.jsx)("input", {
								value: r,
								onChange: (e) => i(e.target.value),
								placeholder: "Tìm mã lô (LO-0308), đối tác (Phú Anh), mã đối tác…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => o((e) => !e),
							className: z("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", a ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, F.jsx)(ua, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					a && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => c((e) => !e),
								className: z("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", s ? "border-amber-400 bg-amber-50 text-amber-800" : "border-slate-200 bg-white text-slate-600"),
								children: [/* @__PURE__ */ (0, F.jsx)(Wr, { size: 16 }), " Chỉ còn phải trả"]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đồng tiền:"
								}), C.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => u(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", l === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đối tác:"
								}), w.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => f(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", d === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : V(ee(e))
								}, e))]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Trạng thái:"
								}), T.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
									onClick: () => m(e),
									className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", p === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, F.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [E.length, " dòng"]
							}),
							" · Ưu tiên theo còn phải trả thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật."
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
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Lô" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Đối tác" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Phải trả" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Đã trả" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Còn lại" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Đồng tiền" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: E.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(P, {
									to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.shipmentId
								}) }),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "font-semibold max-w-[220px]",
									children: [/* @__PURE__ */ (0, F.jsxs)("span", {
										className: "inline-flex items-center gap-1.5",
										children: [
											/* @__PURE__ */ (0, F.jsx)(Pr, {
												size: 15,
												className: "text-[#1e5aa8] shrink-0"
											}),
											" ",
											V(e.partnerName)
										]
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[12px] text-slate-400 font-normal",
										children: e.partnerId
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "font-semibold",
									children: B(e.payable, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "text-blue-700 font-semibold",
									children: B(e.paid, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: z("font-extrabold", !Ba(e.remaining) && (e.remaining ?? 0) > 0 ? "text-amber-800" : "text-slate-500"),
									children: B(e.remaining, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("span", {
									className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
									children: e.currency
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: mo(e.status),
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }), " Mở lô"]
									}), (e.remaining ?? 0) > 0 && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => D(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Oa, { size: 15 }), " Trả đối tác"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [E.map((e) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Ya, { tone: mo(e.status) }),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.shipmentId
									}),
									/* @__PURE__ */ (0, F.jsx)(H, {
										tone: mo(e.status),
										size: "sm",
										children: e.status
									}),
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
										children: e.currency
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: [
									V(e.partnerName),
									" ",
									/* @__PURE__ */ (0, F.jsx)("span", {
										className: "text-slate-400 font-normal text-[12.5px]",
										children: e.partnerId
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 mt-2.5 text-center",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-slate-50 border p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-slate-500 font-semibold",
											children: "Phải trả"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px]",
											children: B(e.payable, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-blue-50 border border-blue-200 p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-blue-700 font-semibold",
											children: "Đã trả"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px] text-blue-700",
											children: B(e.paid, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "rounded-xl bg-amber-50 border border-amber-200 p-2.5",
										children: [/* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[11px] text-amber-700 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-extrabold text-[14px] text-amber-800",
											children: B(e.remaining, e.currency)
										})]
									})
								]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 17 }), " MỞ LÔ"]
						}), (e.remaining ?? 0) > 0 ? /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => D(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Oa, { size: 17 }), " TRẢ ĐỐI TÁC"]
						}) : /* @__PURE__ */ (0, F.jsx)("span", {
							className: "flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]",
							children: "Đã trả đủ"
						})]
					})]
				}, e.id)), E.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Chưa có khoản phải trả đối tác"
					}), /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Chưa có nghĩa vụ / thanh toán canonical nào cho các lô hiện tại — phải trả là “chưa xác định”, không phải 0."
					})]
				})]
			}),
			h && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => g(null)
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Ghi nhận thanh toán đối tác — ", h.shipmentId]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[13.5px] text-slate-500 mt-1",
							children: [
								"Đối tác ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: V(h.partnerName) }),
								" (",
								h.partnerId,
								") · Còn phải trả: ",
								/* @__PURE__ */ (0, F.jsx)("b", {
									className: "text-amber-800",
									children: B(h.remaining, h.currency)
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-3 mt-3",
							children: /* @__PURE__ */ (0, F.jsx)(W, {
								label: `Số tiền (${h.currency})`,
								required: !0,
								error: v ? void 0 : "Nhập số tiền — VD: 20000000",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: v,
									onChange: (e) => y(e.target.value),
									inputMode: "numeric",
									placeholder: "VD: 20000000",
									className: G(v ? "ok" : "missing")
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: [
								"Ghi theo đồng tiền của lô (",
								h.currency,
								") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản trả thứ hai."
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => g(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(Za, {
								onClick: () => {
									if (!h) return;
									let e = Number(v.replace(/\D/g, ""));
									if (!e) {
										n("Chưa nhập số tiền", `Nhập số tiền ${h.currency} rồi bấm Lưu.`, "red");
										return;
									}
									if (!t("partner_payment_record", {
										shipmentId: h.shipmentId,
										partnerId: h.partnerId,
										amount: e,
										currency: h.currency,
										requestId: b.current,
										date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
										note: "Trả đối tác từ bàn công nợ đối tác"
									})) {
										n("Không gửi được", "Component chưa kết nối backend.", "red");
										return;
									}
									n("Đã gửi thanh toán " + B(e, h.currency), "Ghi qua canonical ledger (transaction + allocation) — backend sẽ đọc lại còn phải trả.", "green"), g(null), y("");
								},
								children: "💸 LƯU THANH TOÁN"
							})]
						})
					]
				})]
			}),
			E.length > 0 && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "md:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: /* @__PURE__ */ (0, F.jsxs)(P, {
					to: "/lo-hang",
					className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px] flex items-center justify-center",
					children: ["XEM LÔ HÀNG ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
				})
			})
		]
	});
}
//#endregion
//#region src/pages/Customers.tsx
var go = {
	id: "",
	name: "",
	phone: "",
	email: "",
	contactPerson: "",
	taxCode: "",
	address: "",
	note: ""
};
function _o() {
	let { customers: e, dispatch: t, toast: n, role: r } = Zn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(null), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(!1), [m, h] = (0, _.useState)(go), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)(""), x = (0, _.useMemo)(() => e.filter((e) => !i || (e.id + e.name + e.short + e.mst + e.taxCode + e.phone + e.email).toLowerCase().includes(i.toLowerCase())), [e, i]), S = (e, t) => h((n) => ({
		...n,
		[e]: t
	})), C = () => {
		h(go), s(!0);
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
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Ea, { size: 18 }),
						title: "Khách Hàng",
						sub: "Tìm theo mã · tên · MST · SĐT · email — tạo, sửa, lưu trữ và import qua backend Logistics thật",
						right: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex gap-2",
							children: [/* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: () => p(!0),
								className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(Sa, { size: 17 }), " Import"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: C,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 18 }), " Khách mới"]
							})]
						})
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [/* @__PURE__ */ (0, F.jsx)(R, {
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
										children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 15 }), " Sửa"]
									}), r === "ADMIN" && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => d(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-red-200 text-red-700 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(fr, { size: 15 }), " Lưu trữ"]
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
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Khách mới"]
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
							children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 17 }), " SỬA"]
						}), r === "ADMIN" ? /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => d(e),
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-red-700 min-h-[52px]",
							children: [/* @__PURE__ */ (0, F.jsx)(fr, { size: 17 }), " LƯU TRỮ"]
						}) : /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/kinh-doanh-bao-gia",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: ["BÁO GIÁ ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
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
						children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Khách mới"]
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
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Mã khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.id,
										disabled: !!c,
										onChange: (e) => S("id", e.target.value),
										placeholder: "VD: CUST-ABC",
										className: G(m.id ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Tên khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.name,
										onChange: (e) => S("name", e.target.value),
										placeholder: "Công ty / cá nhân",
										className: G(m.name ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Mã số thuế",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.taxCode,
										onChange: (e) => S("taxCode", e.target.value),
										placeholder: "MST",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Người liên hệ",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.contactPerson,
										onChange: (e) => S("contactPerson", e.target.value),
										placeholder: "Tên người liên hệ",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Số điện thoại",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.phone,
										onChange: (e) => S("phone", e.target.value),
										placeholder: "SĐT",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Email",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: m.email,
										onChange: (e) => S("email", e.target.value),
										placeholder: "email",
										className: G()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Địa chỉ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: m.address,
									onChange: (e) => S("address", e.target.value),
									placeholder: "Địa chỉ kho / văn phòng",
									className: G()
								})
							}), /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Ghi chú",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: m.note,
									onChange: (e) => S("note", e.target.value),
									placeholder: "Ghi chú nội bộ",
									className: G()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => {
									s(!1), l(null);
								},
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsxs)(Za, {
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
									}), n("Đã gửi tạo khách hàng " + e, "Backend ghi + audit; danh sách tự làm mới từ Logistics.", "green")), s(!1), l(null), h(go);
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
							children: /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Lý do lưu trữ",
								required: !0,
								error: g ? void 0 : "Nhập lý do trước khi lưu trữ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: g,
									onChange: (e) => v(e.target.value),
									placeholder: "VD: ngừng hợp tác",
									className: G(g ? "ok" : "missing")
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
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
							children: /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Dữ liệu (mỗi dòng 1 khách)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: y,
									onChange: (e) => b(e.target.value),
									rows: 6,
									placeholder: "CUST-XYZ;Khách XYZ;0109999000;0988111222;xyz@example.com;KCN Test",
									className: z(G(), "font-mono text-[13.5px]")
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => p(!1),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(Xa, {
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
var vo = {
	DRAFT: "Nháp",
	READY_FOR_REVIEW: "Chờ review",
	SENT: "Đã gửi khách",
	ACCEPTED: "Khách chốt",
	REJECTED: "Từ chối",
	EXPIRED: "Hết hạn",
	READY_TO_CREATE_SHIPMENT: "Sẵn sàng tạo lô"
}, yo = {
	DRAFT: "gray",
	READY_FOR_REVIEW: "blue",
	SENT: "amber",
	ACCEPTED: "green",
	REJECTED: "red",
	EXPIRED: "gray",
	READY_TO_CREATE_SHIPMENT: "green"
}, bo = ["USD", "CNY"], xo = {
	code: "",
	serviceName: "",
	unit: "Lần",
	qty: "1",
	currency: "VND",
	costUnit: "",
	sellUnit: "",
	taxPct: "8"
}, So = {
	customerId: "",
	salesOwner: "",
	origin: "",
	destination: "",
	route: "",
	incoterm: "EXW",
	transportMode: "Road",
	goodsDescription: "",
	expectedDeliveryDate: "",
	lines: [{ ...xo }],
	fx: {
		USD: "",
		CNY: ""
	}
}, Co = (e) => e == null ? "" : Number(e).toLocaleString("vi-VN"), wo = (e) => {
	let t = e.fxRatesToVnd ?? {}, n = (e.fxNeededFor ?? []).filter((e) => t[e] != null).map((e) => `${e} ${Co(t[e])}`);
	return n.length ? "Tỷ giá báo giá: " + n.join(" · ") : "";
};
function To(e) {
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
function Eo() {
	let { quotes: e, customers: t, dispatch: n, toast: r } = Zn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("ALL"), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(So), m = (0, _.useMemo)(() => e.filter((e) => (o === "ALL" || e.status === o) && (!i || (e.id + e.quoteNo + e.customer + e.salesOwner + e.origin + e.destination).toLowerCase().includes(i.toLowerCase()))), [
		e,
		i,
		o
	]), h = ["ALL", ...Array.from(new Set(e.map((e) => e.status)))], g = bo.filter((e) => f.lines.some((t) => (t.currency || "VND").trim().toUpperCase() === e)), v = (e, t) => p((n) => ({
		...n,
		[e]: t
	})), y = (e, t) => p((n) => ({
		...n,
		fx: {
			...n.fx,
			[e]: t
		}
	})), b = (e, t, n) => p((r) => ({
		...r,
		lines: r.lines.map((r, i) => i === e ? {
			...r,
			[t]: n
		} : r)
	})), x = () => p((e) => ({
		...e,
		lines: [...e.lines, { ...xo }]
	})), S = (e) => p((t) => ({
		...t,
		lines: t.lines.length > 1 ? t.lines.filter((t, n) => n !== e) : t.lines
	})), C = () => {
		p({
			...So,
			lines: [{ ...xo }],
			fx: {
				USD: "",
				CNY: ""
			},
			salesOwner: "Minh Tú"
		}), l(!0);
	}, w = (e) => {
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
			lines: e.serviceLines.length ? e.serviceLines.map(To) : [{ ...xo }],
			fx: {
				USD: Co(e.fxRatesToVnd?.USD),
				CNY: Co(e.fxRatesToVnd?.CNY)
			}
		}), d(e);
	}, T = () => f.lines.filter((e) => e.code.trim() || e.serviceName.trim()).map((e) => ({
		code: e.code.trim(),
		serviceName: e.serviceName.trim(),
		unit: e.unit.trim() || "Lần",
		qty: e.qty.trim() === "" ? "" : Number(e.qty),
		currency: e.currency.trim() || "VND",
		costUnit: e.costUnit.trim() === "" ? "" : Number(e.costUnit),
		sellUnit: e.sellUnit.trim() === "" ? "" : Number(e.sellUnit),
		taxPct: e.taxPct.trim() === "" ? "" : Number(e.taxPct)
	})), ee = () => {
		if (!f.customerId) {
			r("Chưa chọn khách hàng", "Chọn khách hàng trước khi tạo báo giá.", "red");
			return;
		}
		let e = T();
		if (e.length === 0) {
			r("Thiếu dòng dịch vụ", "Cần ít nhất một dòng dịch vụ báo giá.", "red");
			return;
		}
		let t = bo.filter((t) => e.some((e) => e.currency === t)), i = t.filter((e) => {
			let t = String(f.fx[e] ?? "").replace(/\s|\./g, "").replace(",", "."), n = Number(t);
			return !(t.trim() !== "" && Number.isFinite(n) && n > 0);
		});
		if (i.length > 0) {
			r("Thiếu tỷ giá báo giá", "Cần tỷ giá " + i.map((e) => e + " → VND").join(", ") + " cho các dòng ngoại tệ. Hệ thống không tự đặt tỷ giá.", "red");
			return;
		}
		let a = {};
		for (let e of t) {
			let t = String(f.fx[e]).replace(/\s|\./g, "").replace(",", ".");
			a[e] = Number(t);
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
			serviceLines: e,
			fx: a
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
			serviceLines: e,
			fx: a
		}), r("Đã gửi tạo báo giá", "Backend tạo mã Q-… tự động, tính dự toán và audit.", "green")), l(!1), d(null);
	}, E = (e, t) => {
		n("quote_transition", {
			id: e.id,
			nextStatus: t
		}), r("Đã gửi chuyển trạng thái " + e.id, `→ ${vo[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Ir, { size: 18 }),
						title: "Kinh doanh · Báo giá",
						sub: "Báo giá (estimate) là dự toán LOG-C12 — tách bạch với tài chính thực thu/chi. Tìm theo mã · khách · tuyến.",
						right: /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: C,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 18 }), " Tạo báo giá"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
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
							className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", o === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : vo[e] ?? e
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
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "font-bold",
									children: [Va(e.sellingPriceTotalVnd ?? e.total, "VND"), wo(e) && /* @__PURE__ */ (0, F.jsx)("span", {
										className: "block text-[11.5px] font-semibold text-slate-400",
										children: wo(e)
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(H, {
									tone: yo[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								}) }),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex flex-wrap gap-1.5",
									children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
										onClick: () => E(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: vo[t] ?? t
									}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => w(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Sửa"]
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
							onClick: C,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo báo giá"]
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
									tone: yo[e.status] ?? "gray",
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
								children: [Va(e.sellingPriceTotalVnd ?? e.total, "VND"), " ₫"]
							}),
							wo(e) && /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12px] font-semibold text-slate-400 mt-0.5",
								children: wo(e)
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "border-t p-3 flex flex-wrap gap-2",
						children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: () => E(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: vo[t] ?? t
						}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => w(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Sửa"]
						})]
					})]
				}, e.id)), m.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy báo giá nào"
					}), /* @__PURE__ */ (0, F.jsxs)("button", {
						onClick: C,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo báo giá"]
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
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: f.customerId,
										disabled: !!u,
										onChange: (e) => v("customerId", e.target.value),
										className: G(f.customerId ? "ok" : "missing"),
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
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Sale phụ trách",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.salesOwner,
										onChange: (e) => v("salesOwner", e.target.value),
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Nơi lấy (origin)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.origin,
										onChange: (e) => v("origin", e.target.value),
										placeholder: "VD: Bằng Tường (Quảng Tây)",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Nơi giao (destination)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.destination,
										onChange: (e) => v("destination", e.target.value),
										placeholder: "VD: KCN Quế Võ, Bắc Ninh",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Tuyến / cửa khẩu",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.route,
										onChange: (e) => v("route", e.target.value),
										placeholder: "VD: Hữu Nghị (Lạng Sơn)",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Incoterm",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.incoterm,
										onChange: (e) => v("incoterm", e.target.value),
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Phương thức",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.transportMode,
										onChange: (e) => v("transportMode", e.target.value),
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Ngày giao dự kiến",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: f.expectedDeliveryDate,
										onChange: (e) => v("expectedDeliveryDate", e.target.value),
										placeholder: "VD: 2026-09-20",
										className: G()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsx)(W, {
							label: "Mô tả hàng hóa",
							children: /* @__PURE__ */ (0, F.jsx)("input", {
								value: f.goodsDescription,
								onChange: (e) => v("goodsDescription", e.target.value),
								placeholder: "VD: Linh kiện điện tử",
								className: z(G(), "mt-3")
							})
						}),
						g.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-4 rounded-xl border-2 border-amber-300 bg-amber-50/70 p-3.5",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-extrabold text-[15px] text-amber-900",
									children: "Tỷ giá báo giá — bắt buộc cho dòng ngoại tệ"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] text-amber-800 mt-0.5",
									children: "Tổng VND của báo giá được quy đổi theo tỷ giá bạn nhập ở đây. Hệ thống không tự đặt tỷ giá và đây không phải tỷ giá giao dịch thực tế."
								}),
								/* @__PURE__ */ (0, F.jsx)("div", {
									className: "grid grid-cols-2 gap-2.5 mt-2.5",
									children: g.map((e) => /* @__PURE__ */ (0, F.jsx)(W, {
										label: `Tỷ giá ${e} → VND`,
										required: !0,
										hint: "Số có dấu chấm phân cách hàng nghìn.",
										children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: f.fx[e],
											onChange: (t) => y(e, t.target.value),
											inputMode: "decimal",
											placeholder: e === "USD" ? "VD: 25.500" : "VD: 3.650",
											className: G(f.fx[e].trim() ? "ok" : "missing")
										})
									}, e))
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "flex items-center justify-between mb-2",
								children: [/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-extrabold text-[15px] text-[#0f2a4a]",
									children: "Dòng dịch vụ"
								}), /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: x,
									className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
									children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 15 }), " Thêm dòng"]
								})]
							}), /* @__PURE__ */ (0, F.jsx)("div", {
								className: "space-y-2",
								children: f.lines.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl border border-slate-200 p-3 bg-slate-50/60",
									children: [/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "grid grid-cols-2 md:grid-cols-4 gap-2",
										children: [
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Mã dịch vụ",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.code,
													onChange: (e) => b(t, "code", e.target.value),
													placeholder: "DV-VC-TQ",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Tên dịch vụ",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.serviceName,
													onChange: (e) => b(t, "serviceName", e.target.value),
													placeholder: "Cước xe TQ",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "ĐVT",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.unit,
													onChange: (e) => b(t, "unit", e.target.value),
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Số lượng",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.qty,
													onChange: (e) => b(t, "qty", e.target.value),
													inputMode: "numeric",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Giá vốn (unit)",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.costUnit,
													onChange: (e) => b(t, "costUnit", e.target.value),
													inputMode: "numeric",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Giá bán (unit)",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.sellUnit,
													onChange: (e) => b(t, "sellUnit", e.target.value),
													inputMode: "numeric",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Thuế %",
												children: /* @__PURE__ */ (0, F.jsx)("input", {
													value: e.taxPct,
													onChange: (e) => b(t, "taxPct", e.target.value),
													inputMode: "numeric",
													className: G()
												})
											}),
											/* @__PURE__ */ (0, F.jsx)(W, {
												label: "Tiền tệ",
												children: /* @__PURE__ */ (0, F.jsxs)("select", {
													value: e.currency,
													onChange: (e) => b(t, "currency", e.target.value),
													className: G(),
													children: [
														/* @__PURE__ */ (0, F.jsx)("option", { children: "VND" }),
														/* @__PURE__ */ (0, F.jsx)("option", { children: "USD" }),
														/* @__PURE__ */ (0, F.jsx)("option", { children: "CNY" })
													]
												})
											})
										]
									}), f.lines.length > 1 && /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => S(t),
										className: "mt-2 inline-flex items-center gap-1 text-[13px] font-bold text-red-600",
										children: [/* @__PURE__ */ (0, F.jsx)(ga, { size: 14 }), " Xóa dòng"]
									})]
								}, t))
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => {
									l(!1), d(null);
								},
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsxs)(Za, {
								onClick: ee,
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
var Do = {
	DRAFT: "Nháp",
	REVIEWING: "Đang review",
	AGREED: "Đã đồng ý",
	REVISED: "Đã sửa đổi",
	VOID: "Vô hiệu"
}, Oo = {
	DRAFT: "gray",
	REVIEWING: "blue",
	AGREED: "green",
	REVISED: "amber",
	VOID: "red"
}, ko = [
	"accepted_quotation",
	"signed_contract",
	"customer_confirmation",
	"entrusted_documentation"
], Ao = {
	accepted_quotation: "Báo giá được khách chốt",
	signed_contract: "Hợp đồng đã ký",
	customer_confirmation: "Khách xác nhận (email/tin nhắn)",
	entrusted_documentation: "Chứng từ ủy thác nhập khẩu"
};
function jo() {
	let { agreements: e, quotes: t, dispatch: n, toast: r } = Zn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("ALL"), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)({}), x = (0, _.useMemo)(() => e.filter((e) => (o === "ALL" || e.status === o) && (!i || (e.id + e.agreementNo + e.customer + e.quoteReference).toLowerCase().includes(i.toLowerCase()))), [
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
		for (let n of ko) t[n] = !!e.evidence?.[n];
		b(t), d(e);
	}, ee = () => {
		if (!f) {
			r("Chưa chọn báo giá", "Thỏa thuận chỉ được tạo từ báo giá đã khách chốt (ACCEPTED).", "red");
			return;
		}
		n("agreement_create", { quoteId: f }), r("Đã gửi tạo thỏa thuận", "Backend đóng băng điều khoản thương mại từ báo giá chốt.", "green"), l(!1);
	}, E = () => {
		u && (n("agreement_edit", {
			id: u.id,
			assumptions: m.split("\n").map((e) => e.trim()).filter(Boolean),
			unresolved_issues: g.split("\n").map((e) => e.trim()).filter(Boolean),
			evidence: {
				...ko.reduce((e, t) => ({
					...e,
					[t]: !!y[t]
				}), {}),
				notes: "",
				source: "Bằng chứng đánh dấu thủ công qua work desk; không suy diễn 'đã ký' từ tên file."
			}
		}), r("Đã gửi cập nhật " + u.id, "Backend ghi + audit; bàn giao được tính lại.", "green"), d(null));
	}, D = (e, t) => {
		n("agreement_transition", {
			id: e.id,
			nextStatus: t
		}), r("Đã gửi chuyển trạng thái " + e.id, `→ ${Do[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(mi, { size: 18 }),
						title: "Thỏa thuận mua bán · Bàn giao",
						sub: "Đóng băng điều khoản thương mại từ báo giá đã chốt — KHÔNG phải tài chính thực thu/chi",
						right: /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: w,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 18 }), " Tạo thỏa thuận"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
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
							className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", o === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : Do[e] ?? e
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
									tone: Oo[e.status] ?? "gray",
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
										onClick: () => D(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: Do[t] ?? t
									}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
										onClick: () => T(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Sửa"]
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
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo thỏa thuận"]
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
									tone: Oo[e.status] ?? "gray",
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
							onClick: () => D(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: Do[t] ?? t
						}, t)), /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => T(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, F.jsx)(Yi, { size: 14 }), " Sửa"]
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
						children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo thỏa thuận"]
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
							children: /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Báo giá nguồn",
								required: !0,
								children: /* @__PURE__ */ (0, F.jsxs)("select", {
									value: f,
									onChange: (e) => p(e.target.value),
									className: G(f ? "ok" : "missing"),
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
											Va(e.sellingPriceTotalVnd ?? e.total),
											" ₫"
										]
									}, e.id))]
								})
							})
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => l(!1),
								children: "Hủy"
							}), C.length > 0 ? /* @__PURE__ */ (0, F.jsx)(Za, {
								onClick: ee,
								children: "TẠO"
							}) : /* @__PURE__ */ (0, F.jsx)(Xa, {
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
								children: ko.map((e) => /* @__PURE__ */ (0, F.jsxs)("label", {
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
										children: Ao[e]
									})]
								}, e))
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-3 mt-4",
							children: [/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Giả định thương mại (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: m,
									onChange: (e) => h(e.target.value),
									rows: 4,
									className: G()
								})
							}), /* @__PURE__ */ (0, F.jsx)(W, {
								label: "Vấn đề chưa giải quyết (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, F.jsx)("textarea", {
									value: g,
									onChange: (e) => v(e.target.value),
									rows: 3,
									placeholder: "Các vấn đề chặn bàn giao vận hành",
									className: G()
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
								onClick: () => d(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, F.jsx)(Xa, {
								onClick: E,
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
function Mo() {
	let { contracts: e } = Zn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)("ALL"), a = (0, _.useMemo)(() => e.filter((e) => (r === "ALL" || e.kind === r) && (!t || (e.id + e.contractNo + e.client + e.company + e.agent).toLowerCase().includes(t.toLowerCase()))), [
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
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(bi, { size: 18 }),
						title: "Hợp đồng",
						sub: "HDMB · HDNT · PL — tìm theo số hợp đồng, khách, công ty, đại lý",
						right: /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/hop-dong/moi",
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 18 }), " Tạo hợp đồng"]
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, F.jsx)(R, {
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
							className: z("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", r === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
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
									children: Va(e.value, e.currency)
								}),
								/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("div", {
									className: "flex gap-1.5",
									children: /* @__PURE__ */ (0, F.jsxs)(P, {
										to: "/hop-dong/" + e.id,
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]",
										children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }), " MỞ"]
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
							children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo hợp đồng"]
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
								children: Va(e.value, e.currency)
							})
						]
					}), /* @__PURE__ */ (0, F.jsx)("div", {
						className: "border-t",
						children: /* @__PURE__ */ (0, F.jsxs)(P, {
							to: "/hop-dong/" + e.id,
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: ["MỞ HỢP ĐỒNG ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
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
						children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 17 }), " Tạo hợp đồng"]
					})]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/ContractDetail.tsx
var No = [
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
], Po = {
	READY: "green",
	GENERATED: "blue",
	MISSING_INFO: "amber",
	NOT_APPLICABLE: "gray",
	OWNER_RULE_REQUIRED: "amber",
	BLOCKED: "red",
	DEFERRED: "gray",
	ISSUED: "green"
}, Fo = {
	READY: "Sẵn sàng",
	GENERATED: "Đã sinh",
	MISSING_INFO: "Thiếu thông tin",
	NOT_APPLICABLE: "Không áp dụng",
	OWNER_RULE_REQUIRED: "Cần quy tắc chủ",
	BLOCKED: "Bị chặn",
	DEFERRED: "Hoãn lại",
	ISSUED: "Đã phát hành"
};
function Io(e) {
	return {
		description: e.description,
		unit: e.unit,
		quantity: e.quantity == null ? "" : String(e.quantity),
		unitPrice: e.unitPrice == null ? "" : String(e.unitPrice)
	};
}
function Lo() {
	let { id: e } = Tt(), [t, n] = Vn(), r = t.get("tab") || "tong-quan", { contracts: i, authority: a, shipments: o, dispatch: s, toast: c } = Zn(), l = Ct(), u = i.find((t) => t.id === e), [d, f] = (0, _.useState)({}), [p, m] = (0, _.useState)([]), [h, g] = (0, _.useState)(""), v = (e) => {
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
		}), m(e.goodsLines.length ? e.goodsLines.map(Io) : [{
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
	}, ee = (e, t) => {
		s("contract_docgen_issue", {
			documentId: e,
			revision: t
		}), c("Đã gửi phát hành " + e, "Chứng từ ISSUED sẽ bất biến (không sửa/xóa).", "blue");
	}, E = () => {
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
	let D = u.thresholdVnd ?? 5e7, O = u.goodsTotals != null && u.goodsTotals.total_after_vat < D, te = o.filter((e) => !u.linkedShipments.some((t) => t.id === e.id));
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("button", {
				onClick: () => l(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, F.jsx)(gr, { size: 17 }), " Quay lại"]
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
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Công ty (mua)",
										value: V(u.company)
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Đại lý (bán)",
										value: V(u.agent)
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
										label: "Giá trị",
										value: Ha(u.value)
									}),
									/* @__PURE__ */ (0, F.jsx)(to, {
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
						children: No.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
							onClick: () => n({ tab: e.id }),
							className: z("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", r === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
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
						children: [/* @__PURE__ */ (0, F.jsx)(bi, {
							size: 19,
							className: "text-[#1e5aa8]"
						}), " Danh tính pháp lý"]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid sm:grid-cols-2 gap-3",
						children: [
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Số HDNT",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdnt_no,
									onChange: (e) => y("hdnt_no", e.target.value),
									placeholder: "HDNT-…/2026",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Ngày HDNT",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdnt_date,
									onChange: (e) => y("hdnt_date", e.target.value),
									placeholder: "2026-09-01",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Hiệu lực từ",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.valid_from,
									onChange: (e) => y("valid_from", e.target.value),
									placeholder: "2026-09-01",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Hiệu lực đến",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.valid_to,
									onChange: (e) => y("valid_to", e.target.value),
									placeholder: "2027-08-31",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Số PL",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.pl_no,
									onChange: (e) => y("pl_no", e.target.value),
									placeholder: "PL-…/2026",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Ngày PL",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.pl_date,
									onChange: (e) => y("pl_date", e.target.value),
									placeholder: "2026-09-02",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Số HDMB",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdmb_no,
									onChange: (e) => y("hdmb_no", e.target.value),
									placeholder: "HDMB-…/2026",
									className: G()
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(W, {
								label: "Ngày HDMB",
								children: /* @__PURE__ */ (0, F.jsx)("input", {
									value: d.hdmb_date,
									onChange: (e) => y("hdmb_date", e.target.value),
									placeholder: "2026-09-03",
									className: G()
								})
							})
						]
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, F.jsx)(Er, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Đối tác & thông tin chung"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Công ty (bên mua)",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.company_id,
										onChange: (e) => y("company_id", e.target.value),
										className: G(d.company_id ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, F.jsx)("option", {
											value: "",
											children: "-- Chọn công ty --"
										}), a.companies.map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
											value: e.id,
											children: e.legalName
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Đại lý (bên bán)",
									required: !0,
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.agent_id,
										onChange: (e) => y("agent_id", e.target.value),
										className: G(d.agent_id ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, F.jsx)("option", {
											value: "",
											children: "-- Chọn đại lý --"
										}), a.agents.map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
											value: e.id,
											children: e.legalName
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Loại",
									children: /* @__PURE__ */ (0, F.jsxs)("select", {
										value: d.kind,
										onChange: (e) => y("kind", e.target.value),
										className: G(),
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
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Giá trị (VND)",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.value,
										onChange: (e) => y("value", e.target.value),
										inputMode: "numeric",
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Tiền tệ",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.currency,
										onChange: (e) => y("currency", e.target.value),
										className: G()
									})
								}),
								/* @__PURE__ */ (0, F.jsx)(W, {
									label: "Ghi chú",
									children: /* @__PURE__ */ (0, F.jsx)("input", {
										value: d.note,
										onChange: (e) => y("note", e.target.value),
										className: G()
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
						/* @__PURE__ */ (0, F.jsx)(Xa, {
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
								children: [/* @__PURE__ */ (0, F.jsx)(qi, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Hàng hóa hợp đồng"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: x,
								className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
								children: [/* @__PURE__ */ (0, F.jsx)($i, { size: 15 }), " Thêm dòng"]
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
											className: G()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.unit,
											onChange: (e) => b(t, "unit", e.target.value),
											placeholder: "Bộ / chiếc",
											className: G()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.quantity,
											onChange: (e) => b(t, "quantity", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: G()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("input", {
											value: e.unitPrice,
											onChange: (e) => b(t, "unitPrice", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: G()
										}) }),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "text-slate-600",
											children: "8%"
										}),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-bold whitespace-nowrap",
											children: Ba(i) ? "—" : Va(i)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)("button", {
											onClick: () => S(t),
											className: "touch-target inline-flex items-center justify-center w-9 h-9 rounded-lg text-red-600 hover:bg-red-50",
											"aria-label": "Xóa dòng",
											children: /* @__PURE__ */ (0, F.jsx)(ga, { size: 16 })
										}) })
									] }, t);
								}) })]
							})
						}),
						/* @__PURE__ */ (0, F.jsx)(Xa, {
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
										children: Va(u.goodsTotals?.subtotal)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-slate-500 font-semibold",
										children: "VAT 8%"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px]",
										children: Va(u.goodsTotals?.vat_amount)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-blue-700 font-semibold",
										children: "Sau thuế"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px] text-blue-700",
										children: Va(u.goodsTotals?.total_after_vat)
									})]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-violet-50 border border-violet-200 p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-violet-700 font-semibold",
										children: "Ngưỡng"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[17px] text-violet-700",
										children: Va(D)
									})]
								})
							]
						}),
						u.goodsTotals == null ? /* @__PURE__ */ (0, F.jsx)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13.5px] text-amber-900",
							children: "Chưa có tổng đáng tin cậy (có dòng UNKNOWN) — không thể thay bằng 0, chứng từ bị chặn cho tới khi đủ dữ liệu."
						}) : /* @__PURE__ */ (0, F.jsxs)("div", {
							className: z("mt-3 rounded-xl border-2 p-3.5", O ? "border-emerald-300 bg-emerald-50" : "border-blue-300 bg-blue-50"),
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "font-extrabold text-[15px]",
								children: O ? "Sau thuế < 50.000.000 ₫ → HDNT + PL" : "Sau thuế ≥ 50.000.000 ₫ → HDMB"
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
								children: [/* @__PURE__ */ (0, F.jsx)(mi, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Chứng từ HDNT · PL · HDMB"]
							}), /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: T,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, F.jsx)(ma, { size: 17 }), " SINH CHỨNG TỪ"]
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
											tone: Po[e.state] ?? "gray",
											size: "sm",
											children: Fo[e.state] ?? e.state
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
									className: z("w-9 h-9 rounded-lg grid place-items-center shrink-0", e.status === "ISSUED" ? "bg-emerald-600 text-white" : "bg-blue-100 text-blue-700"),
									children: e.status === "ISSUED" ? /* @__PURE__ */ (0, F.jsx)(Kr, { size: 18 }) : /* @__PURE__ */ (0, F.jsx)(bi, { size: 18 })
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
									onClick: () => qa(e.fileName, e.downloadBase64, e.mime),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, F.jsx)(oi, { size: 16 }), " Tải"]
								}),
								e.status !== "ISSUED" && /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => ee(e.documentId, e.revision),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 text-white font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, F.jsx)(ma, { size: 15 }), " Phát hành"]
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
						children: [/* @__PURE__ */ (0, F.jsx)(Mi, {
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
									children: /* @__PURE__ */ (0, F.jsx)(qi, { size: 18 })
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
									children: ["MỞ ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })]
								})
							]
						}, e.id))
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
						children: "Liên kết lô mới"
					}), te.length === 0 ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Tất cả lô đã được liên kết."
					}) : /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3",
						children: [/* @__PURE__ */ (0, F.jsx)(W, {
							label: "Chọn lô hàng",
							required: !0,
							children: /* @__PURE__ */ (0, F.jsxs)("select", {
								value: h,
								onChange: (e) => g(e.target.value),
								className: G(h ? "ok" : "missing"),
								children: [/* @__PURE__ */ (0, F.jsx)("option", {
									value: "",
									children: "-- Chọn lô --"
								}), te.map((e) => /* @__PURE__ */ (0, F.jsxs)("option", {
									value: e.id,
									children: [
										e.id,
										" · ",
										e.customer
									]
								}, e.id))]
							})
						}), /* @__PURE__ */ (0, F.jsx)(Xa, {
							onClick: E,
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
function Ro() {
	let { customers: e, dispatch: t, toast: n } = Zn(), r = Ct(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)("HDMB"), [u, d] = (0, _.useState)("");
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[760px]",
		children: [/* @__PURE__ */ (0, F.jsxs)("button", {
			onClick: () => r(-1),
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, F.jsx)(gr, { size: 17 }), " Quay lại"]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-6",
			children: [
				/* @__PURE__ */ (0, F.jsx)(U, {
					icon: /* @__PURE__ */ (0, F.jsx)(bi, { size: 18 }),
					title: "Tạo hợp đồng mới",
					sub: "HDMB / HDNT + Phụ lục — sau khi tạo sẽ nhập hàng hóa, sinh chứng từ và liên kết lô"
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid sm:grid-cols-2 gap-3",
					children: [/* @__PURE__ */ (0, F.jsx)(W, {
						label: "Số hợp đồng",
						required: !0,
						error: i ? void 0 : "Nhập số hợp đồng",
						children: /* @__PURE__ */ (0, F.jsx)("input", {
							value: i,
							onChange: (e) => a(e.target.value),
							placeholder: "VD: HDMB-0310",
							className: G(i ? "ok" : "missing")
						})
					}), /* @__PURE__ */ (0, F.jsx)(W, {
						label: "Loại hợp đồng",
						required: !0,
						children: /* @__PURE__ */ (0, F.jsxs)("select", {
							value: c,
							onChange: (e) => l(e.target.value),
							className: G(),
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
					children: [/* @__PURE__ */ (0, F.jsx)(W, {
						label: "Khách hàng / đối tác",
						required: !0,
						error: o ? void 0 : "Chọn khách hàng",
						children: /* @__PURE__ */ (0, F.jsxs)("select", {
							value: o,
							onChange: (e) => s(e.target.value),
							className: G(o ? "ok" : "missing"),
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
					}), /* @__PURE__ */ (0, F.jsx)(W, {
						label: "Ghi chú",
						children: /* @__PURE__ */ (0, F.jsx)("input", {
							value: u,
							onChange: (e) => d(e.target.value),
							placeholder: "Ghi chú nội bộ",
							className: G()
						})
					})]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid grid-cols-2 gap-2.5 mt-5",
					children: [/* @__PURE__ */ (0, F.jsx)(Qa, {
						onClick: () => r(-1),
						children: "Hủy"
					}), /* @__PURE__ */ (0, F.jsx)(Xa, {
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
//#region src/pages/TariffLookup.tsx
function zo(e) {
	return e || "—";
}
function Bo({ row: e, stacked: t }) {
	return e.fields.length ? /* @__PURE__ */ (0, F.jsx)("span", {
		className: z("text-[13.5px] text-slate-700", t && "block"),
		children: e.fields.map((e) => /* @__PURE__ */ (0, F.jsxs)("span", {
			className: z(!t && "mr-3 whitespace-nowrap"),
			children: [
				/* @__PURE__ */ (0, F.jsxs)("span", {
					className: "font-semibold text-slate-500",
					children: [e.label, ":"]
				}),
				" ",
				/* @__PURE__ */ (0, F.jsx)("span", {
					className: "font-bold",
					children: zo(e.value)
				})
			]
		}, e.label))
	}) : /* @__PURE__ */ (0, F.jsx)("span", {
		className: "text-slate-400",
		children: "—"
	});
}
function Vo() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.tariff ?? null, [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(""), a = r.length > 0 && r !== (e?.query ?? ""), o = e?.rows ?? [], s = !!e?.searched && !a, c = () => {
		let e = t.trim();
		e.length < 2 || (i(e), te("tariff_lookup", { query: e }));
	}, l = e?.source, u = e?.provenance;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(R, { size: 18 }),
						title: "Tra cứu HS & Thuế",
						sub: "Tra cứu mã HS và mô tả hàng hóa tại cơ sở dữ liệu tham chiếu nội bộ — nhập mã HS (chính xác hoặc một phần) hoặc tên hàng."
					}),
					/* @__PURE__ */ (0, F.jsxs)("form", {
						className: "flex flex-col md:flex-row gap-2.5",
						onSubmit: (e) => {
							e.preventDefault(), c();
						},
						children: [/* @__PURE__ */ (0, F.jsx)("input", {
							value: t,
							onChange: (e) => n(e.target.value),
							placeholder: "Ví dụ: 9401, 9403.20 hoặc ghế gỗ…",
							className: "flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] font-mono placeholder:font-sans focus:border-[#1e5aa8] outline-none",
							"aria-label": "Mã HS hoặc tên hàng"
						}), /* @__PURE__ */ (0, F.jsxs)("button", {
							type: "submit",
							disabled: t.trim().length < 2,
							className: "btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-40 disabled:pointer-events-none",
							children: [/* @__PURE__ */ (0, F.jsx)(R, { size: 17 }), " Tra cứu"]
						})]
					}),
					l && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: z("mt-3 rounded-xl border p-3 flex items-start gap-2.5 text-[13px]", l.configured && l.rows ? "border-slate-200 bg-slate-50 text-slate-600" : "border-amber-200 bg-amber-50 text-amber-900"),
						children: [/* @__PURE__ */ (0, F.jsx)(ii, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, F.jsxs)("div", { children: [l.configured && l.rows ? /* @__PURE__ */ (0, F.jsxs)("p", { children: [
							"Nguồn nội bộ: ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "tariff_table" }),
							" · ",
							l.rows.toLocaleString("vi-VN"),
							" dòng ·",
							" ",
							/* @__PURE__ */ (0, F.jsx)("span", {
								className: "font-mono text-[12px] break-all",
								children: l.path
							})
						] }) : /* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-semibold",
							children: l.note
						}), e?.truncated && /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "mt-1 font-semibold",
							children: [
								"Kết quả bị giới hạn ",
								e.limit,
								" dòng — hãy nhập mã HS cụ thể hơn."
							]
						})] })]
					}),
					u && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-2.5 rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/60 p-3 flex items-start gap-2.5 text-[13px] text-amber-900",
						children: [/* @__PURE__ */ (0, F.jsx)(va, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, F.jsx)("p", { children: u.note })]
					})
				]
			}),
			a && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, F.jsxs)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: [
						"Đang tra cứu “",
						r,
						"”…"
					]
				})
			}),
			!a && !s && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(R, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Bảng kết quả đang trống"
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: [
							"Nhập mã HS hoặc tên hàng phía trên rồi bấm ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "Tra cứu" }),
							"."
						]
					})
				]
			}),
			s && e && o.length === 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(wi, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Không tìm thấy kết quả"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: e.reason
					})
				]
			}),
			s && e && o.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "space-y-4",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13.5px] font-semibold text-slate-500 px-1",
						children: [
							"Tìm thấy ",
							e.count.toLocaleString("vi-VN"),
							" dòng khớp “",
							e.query,
							"” — mã HS và mô tả theo dữ liệu tham chiếu nội bộ."
						]
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
						children: /* @__PURE__ */ (0, F.jsx)("div", {
							className: "overflow-x-auto",
							children: /* @__PURE__ */ (0, F.jsxs)("table", {
								className: "tbl w-full text-[14.5px]",
								children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, F.jsx)("th", {
										className: "w-[150px]",
										children: "Mã HS"
									}),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Mô tả tiếng Việt" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Mô tả tiếng Anh" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Thông tin khác (nguyên văn)" })
								] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: o.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("tr", {
									className: "hover:bg-slate-50",
									children: [
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-mono font-extrabold text-[15px] text-[#0f2a4a] whitespace-nowrap",
											children: zo(e.hsCode)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-semibold",
											children: zo(e.descriptionVi)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "text-slate-600",
											children: zo(e.descriptionEn)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: /* @__PURE__ */ (0, F.jsx)(Bo, { row: e }) })
									]
								}, (e.hsCode ?? "?") + t)) })]
							})
						})
					}),
					/* @__PURE__ */ (0, F.jsx)("div", {
						className: "md:hidden space-y-3",
						children: o.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl bg-white border border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "font-mono font-extrabold text-[17px] text-[#0f2a4a] break-all",
									children: zo(e.hsCode)
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[15px] font-semibold text-slate-800 mt-1.5",
									children: zo(e.descriptionVi)
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] text-slate-500 mt-0.5",
									children: zo(e.descriptionEn)
								}),
								e.fields.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-2.5 rounded-xl bg-slate-50 border border-slate-200 p-3",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
										children: "Thông tin khác (nguyên văn)"
									}), /* @__PURE__ */ (0, F.jsx)("div", {
										className: "mt-1",
										children: /* @__PURE__ */ (0, F.jsx)(Bo, {
											row: e,
											stacked: !0
										})
									})]
								})
							]
						}, (e.hsCode ?? "?") + t))
					})
				]
			})
		]
	});
}
//#endregion
//#region src/pages/TranslationWorkspace.tsx
function Ho(e) {
	return typeof TextEncoder < "u" ? new TextEncoder().encode(e).length : e.length;
}
function Uo(e, t, n) {
	return `${t}\u0000${n}\u0000${e}`;
}
function Wo({ label: e, value: t, options: n, onChange: r, disabled: i }) {
	return /* @__PURE__ */ (0, F.jsxs)("label", {
		className: "block flex-1 min-w-0",
		children: [/* @__PURE__ */ (0, F.jsx)("span", {
			className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("select", {
			value: t,
			disabled: i,
			onChange: (e) => r(e.target.value),
			className: z(G(), "disabled:opacity-50"),
			"aria-label": e,
			children: n.map((e) => /* @__PURE__ */ (0, F.jsx)("option", {
				value: e.code,
				children: e.label
			}, e.code))
		})]
	});
}
function Go() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.translation ?? null, t = e?.capability ?? null, n = e?.request ?? null, r = e?.result ?? null, [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("AUTO"), [c, l] = (0, _.useState)("VI"), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)("idle"), m = t?.maxTextBytes ?? 1e5, h = (0, _.useMemo)(() => Ho(i), [i]), g = h > m, v = t?.configured ?? !1, y = t?.allowed ?? !1, b = n ? Uo(n.text, n.sourceLang, n.targetLang) : null, x = u !== null && u !== b, w = v && y && i.trim().length > 0 && !g && !x, T = r?.status === "translated" ? r.text ?? "" : "", ee = () => {
		w && (p("idle"), d(Uo(i, o, c)), te("translate_text", {
			text: i,
			sourceLang: o,
			targetLang: c
		}));
	}, E = () => {
		if (!t) return;
		let e = t.swapSource[c], n = t.swapTarget[o];
		e && s(e), n && l(n);
	}, D = () => {
		a(""), d(null), p("idle");
	}, O = async () => {
		if (T) try {
			await navigator.clipboard.writeText(T), p("done");
		} catch {
			p("failed");
		}
	}, k = t?.sourceLanguages ?? [], ne = t?.targetLanguages ?? [], re = r && r.status !== "translated" ? r.error : null;
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1100px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Oi, { size: 18 }),
						title: "Dịch thuật",
						sub: `Dịch văn bản nghiệp vụ logistics qua ${t?.provider ?? "nhà cung cấp dịch"} — nhập hoặc dán nội dung, chọn cặp ngôn ngữ rồi bấm Dịch.`
					}),
					t && !v && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mb-3 rounded-xl border border-amber-300 bg-amber-50 p-3 flex items-start gap-2.5 text-[13.5px] text-amber-900",
						children: [/* @__PURE__ */ (0, F.jsx)(ia, {
							size: 17,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("p", {
							className: "font-extrabold",
							children: "Translation service chưa được cấu hình"
						}), /* @__PURE__ */ (0, F.jsx)("p", {
							className: "mt-0.5",
							children: t.configNotice
						})] })]
					}),
					t && v && !y && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mb-3 rounded-xl border border-red-200 bg-red-50 p-3 flex items-start gap-2.5 text-[13.5px] text-red-800",
						children: [/* @__PURE__ */ (0, F.jsx)(ia, {
							size: 17,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "font-semibold",
							children: [
								"Vai trò hiện tại không có quyền dịch thuật (quyền ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: "translation" }),
								")."
							]
						})]
					}),
					t?.externalProvider && /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mb-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-3 flex items-start gap-2.5 text-[13px] text-slate-600",
						children: [/* @__PURE__ */ (0, F.jsx)(wi, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, F.jsx)("p", { children: t.privacyNotice })]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-col md:flex-row md:items-end gap-2.5",
						children: [
							/* @__PURE__ */ (0, F.jsx)(Wo, {
								label: "Ngôn ngữ nguồn",
								value: o,
								options: k,
								onChange: s
							}),
							/* @__PURE__ */ (0, F.jsx)("div", {
								className: "md:pb-1",
								children: /* @__PURE__ */ (0, F.jsxs)("button", {
									type: "button",
									onClick: E,
									"aria-label": "Đổi chiều dịch",
									title: "Đổi chiều dịch",
									className: "btn-press touch-target w-full md:w-auto inline-flex items-center justify-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-4 min-h-[48px] hover:bg-slate-50",
									children: [/* @__PURE__ */ (0, F.jsx)(mr, { size: 17 }), " Đổi chiều"]
								})
							}),
							/* @__PURE__ */ (0, F.jsx)(Wo, {
								label: "Ngôn ngữ đích",
								value: c,
								options: ne,
								onChange: l
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("label", {
						className: "block mt-3",
						children: [/* @__PURE__ */ (0, F.jsx)("span", {
							className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
							children: "Văn bản nguồn"
						}), /* @__PURE__ */ (0, F.jsx)("textarea", {
							value: i,
							onChange: (e) => {
								a(e.target.value), d(null);
							},
							placeholder: "Dán nội dung cần dịch: email khách, mô tả hàng hóa, chứng từ…",
							"aria-label": "Văn bản nguồn",
							className: "w-full rounded-xl border-2 border-slate-200 bg-white px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] focus:border-[#1e5aa8] outline-none resize-y"
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: z("mt-1 text-[13px]", g ? "text-red-700 font-semibold" : "text-slate-500"),
						children: [
							"Kích thước: ",
							h.toLocaleString("vi-VN"),
							" /",
							" ",
							m.toLocaleString("vi-VN"),
							" bytes",
							g && " — nội dung quá lớn cho một yêu cầu, hãy rút gọn."
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-col sm:flex-row gap-2.5 mt-3",
						children: [/* @__PURE__ */ (0, F.jsx)(Xa, {
							onClick: ee,
							disabled: !w,
							className: "flex-1",
							children: x ? /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsx)(Ii, {
								size: 17,
								className: "animate-spin"
							}), " Đang dịch…"] }) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsx)(Oi, { size: 17 }), " Dịch"] })
						}), /* @__PURE__ */ (0, F.jsxs)(Qa, {
							onClick: D,
							className: "sm:w-auto",
							children: [/* @__PURE__ */ (0, F.jsx)(ci, { size: 17 }), " Xóa nội dung nhập"]
						})]
					})
				]
			}),
			x && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: [/* @__PURE__ */ (0, F.jsx)(Ii, {
					size: 24,
					className: "mx-auto animate-spin text-[#1e5aa8]"
				}), /* @__PURE__ */ (0, F.jsxs)("p", {
					className: "text-[15px] font-semibold text-slate-500 mt-2",
					children: [
						"Đang dịch qua ",
						t?.provider ?? "nhà cung cấp dịch",
						"…"
					]
				})]
			}),
			!x && re && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-2.5",
				children: [/* @__PURE__ */ (0, F.jsx)(va, {
					size: 18,
					className: "shrink-0 mt-0.5 text-red-600"
				}), /* @__PURE__ */ (0, F.jsxs)("div", { children: [/* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[15px] font-extrabold text-red-800",
					children: r?.status === "config_required" ? "Translation service chưa được cấu hình" : "Chưa dịch được nội dung này"
				}), /* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[14px] text-red-700 mt-0.5",
					children: re
				})] })]
			}),
			!x && r?.status === "translated" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-wrap items-center justify-between gap-2 mb-2",
						children: [/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "text-[16px] font-extrabold text-[#0f2a4a]",
							children: "Kết quả dịch"
						}), /* @__PURE__ */ (0, F.jsx)("div", {
							className: "flex flex-wrap gap-2",
							children: /* @__PURE__ */ (0, F.jsx)("button", {
								type: "button",
								onClick: O,
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px] hover:bg-slate-50",
								children: f === "done" ? /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsx)(Br, {
									size: 16,
									className: "text-emerald-600"
								}), " Đã sao chép"] }) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsx)(ni, { size: 16 }), " Sao chép"] })
							})
						})]
					}),
					f === "failed" && /* @__PURE__ */ (0, F.jsx)("p", {
						className: "mb-2 text-[13px] text-amber-800 font-semibold",
						children: "Trình duyệt không cho phép sao chép tự động — hãy bôi đen bản dịch rồi sao chép thủ công."
					}),
					/* @__PURE__ */ (0, F.jsx)("textarea", {
						readOnly: !0,
						value: T,
						"aria-label": "Bản dịch",
						className: "w-full rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] resize-y whitespace-pre-wrap"
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[13px] text-slate-500 mt-2",
						children: [
							"Ngôn ngữ nguồn phát hiện:",
							" ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: r.detectedSourceLanguage ?? "—" }),
							" · Ký tự tính phí:",
							" ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: r.billedCharacters === null ? "—" : r.billedCharacters.toLocaleString("vi-VN") }),
							" ",
							"· ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: r.apiLabel ?? "—" })
						]
					}),
					n && /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-1",
						children: [
							"Yêu cầu: ",
							n.sourceLang,
							" → ",
							n.targetLang,
							" · bản dịch giữ nguyên xuống dòng, số, mã HS và mã chứng từ như nhà cung cấp trả về."
						]
					})
				]
			}),
			!x && !r && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(Oi, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có bản dịch"
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: [
							"Nhập văn bản, chọn cặp ngôn ngữ rồi bấm ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "Dịch" }),
							". Hệ thống không hiển thị kết quả mẫu thay thế."
						]
					})
				]
			})
		]
	});
}
//#endregion
//#region src/pages/PartnerContext.tsx
var Ko = {
	CONFIRMED: "blue",
	REVIEW_REQUIRED: "amber",
	KNOWN: "green",
	UNKNOWN: "gray"
}, qo = (e) => Ko[(e ?? "").toUpperCase()] ?? "gray";
function Jo({ label: e, value: t, mono: n }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-xl bg-slate-50 border border-slate-200 p-3",
		children: [/* @__PURE__ */ (0, F.jsx)("p", {
			className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("p", {
			className: z("mt-0.5 font-semibold text-[14.5px] break-words", n && "font-mono"),
			children: V(t)
		})]
	});
}
function Yo({ label: e, value: t, ccy: n, strong: r }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: z("rounded-xl border p-2.5 text-center", r ? "bg-amber-50 border-amber-200" : "bg-white border-slate-200"),
		children: [/* @__PURE__ */ (0, F.jsx)("p", {
			className: z("text-[11px] font-semibold", r ? "text-amber-700" : "text-slate-500"),
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("p", {
			className: z("font-extrabold text-[14px]", r ? "text-amber-800" : "text-[#0f2a4a]"),
			children: Ba(t) ? `— ${n ?? ""}`.trim() : B(t, n)
		})]
	});
}
function Xo({ row: e }) {
	let t = [
		e.role ? `Vai trò: ${e.role}` : null,
		e.route ? `Tuyến: ${e.route}` : null,
		e.requiredDate ? `Khách cần giao: ${e.requiredDate}` : null,
		e.plannedDate ? `Kế hoạch: ${e.plannedDate}` : null,
		e.status ? `Trạng thái: ${e.status}` : null
	].filter(Boolean);
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-2xl bg-white border border-slate-200 p-4",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex items-center gap-2 flex-wrap",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] break-all",
						children: e.shipmentId
					}),
					e.status ? /* @__PURE__ */ (0, F.jsx)(H, {
						tone: "blue",
						size: "sm",
						children: e.status
					}) : /* @__PURE__ */ (0, F.jsxs)(H, {
						tone: "gray",
						size: "sm",
						children: ["trạng thái ", "—"]
					}),
					e.financeCurrencies.map((e) => /* @__PURE__ */ (0, F.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
						children: e
					}, e)),
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "ml-auto shrink-0",
						children: e.canOpen ? /* @__PURE__ */ (0, F.jsx)(H, {
							tone: "green",
							size: "sm",
							children: "mở được"
						}) : /* @__PURE__ */ (0, F.jsx)(H, {
							tone: "amber",
							size: "sm",
							children: "không mở được"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "text-[13.5px] text-slate-600 mt-1.5 leading-relaxed",
				children: t.length ? t.join(" · ") : "Bối cảnh lô đang —"
			}),
			e.attention ? /* @__PURE__ */ (0, F.jsxs)("p", {
				className: "text-[13.5px] mt-1.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800",
				children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
					size: 15,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, F.jsxs)("span", { children: [e.attention, e.attentionDetail ? ` — ${e.attentionDetail}` : ""] })]
			}) : null,
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex flex-wrap items-center gap-2 mt-3",
				children: [e.canOpen ? /* @__PURE__ */ (0, F.jsxs)(P, {
					to: e.openHref,
					className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13.5px] px-4 min-h-[48px]",
					children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 16 }), " Mở lô"]
				}) : /* @__PURE__ */ (0, F.jsxs)("span", {
					className: "touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13.5px] px-4 min-h-[48px]",
					children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 15 }), " Lô không có trong dữ liệu hiện tại"]
				}), /* @__PURE__ */ (0, F.jsxs)("span", {
					className: "text-[12px] text-slate-400 break-words",
					children: ["nguồn: ", V(e.source)]
				})]
			})
		]
	});
}
function Zo() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.partnerContext ?? null, [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(null), a = e?.options ?? [], o = e?.selectedKey ?? null, s = (0, _.useMemo)(() => {
		let e = t.trim().toLowerCase();
		return e ? a.filter((t) => [
			t.key,
			t.label,
			t.legalCode,
			t.phone,
			t.email
		].some((t) => (t ?? "").toLowerCase().includes(e))) : a;
	}, [a, t]), c = r !== null && r !== o, l = !!o && !c, u = (e) => {
		i(e), te("partner_context_select", { entityKey: e });
	}, d = () => {
		i(null), te("partner_context_select", { entityKey: "" });
	}, f = e?.identity ?? null, p = f?.party ?? null, m = e?.finance ?? null, h = m?.rows ?? [], g = e?.shipments ?? [], v = e?.documents ?? [], y = (0, _.useMemo)(() => new Set(g.filter((e) => e.canOpen).map((e) => e.shipmentId.toLowerCase())), [g]), b = e?.gaps ?? [], x = e?.unavailable ?? [];
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Si, {
							size: 20,
							className: "text-[#1e5aa8]"
						}),
						title: "Ngữ cảnh Đối tác",
						sub: "Tra cứu đối tác/đại lý và đọc ngữ cảnh đã có trong hệ thống: hồ sơ pháp lý master, các lô liên kết, công nợ phải trả theo từng lô. Màn hình chỉ đọc — không sửa, không ghi.",
						right: /* @__PURE__ */ (0, F.jsxs)("span", {
							className: "hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-[12px] font-bold text-slate-600",
							children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 13 }), " CHỈ ĐỌC"]
						})
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [/* @__PURE__ */ (0, F.jsx)(R, {
							size: 19,
							className: "ml-3.5 text-slate-400 shrink-0"
						}), /* @__PURE__ */ (0, F.jsx)("input", {
							value: t,
							onChange: (e) => n(e.target.value),
							placeholder: "Tìm theo mã đối tác, tên, điện thoại hoặc email…",
							"aria-label": "Tìm đối tác",
							className: "w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
						})]
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[12.5px] text-slate-500 mt-1.5",
						children: [
							"Chỉ tìm trong ",
							(e?.searchFields ?? []).length,
							" trường hệ thống thật sự lưu:",
							(e?.searchFields ?? []).map((e) => ` ${e}`).join(" · ")
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-3",
						children: [a.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có đối tác nào trong dữ liệu hiện tại — trạng thái là ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
								", không có danh sách mẫu."
							]
						}) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] font-bold uppercase tracking-wide text-slate-500 mb-2",
								children: [
									s.length,
									" / ",
									e?.optionCount ?? 0,
									" đối tác",
									e?.optionTruncated ? ` (giới hạn ${e.optionLimit})` : ""
								]
							}),
							/* @__PURE__ */ (0, F.jsx)("div", {
								className: "flex flex-wrap gap-2",
								children: s.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
									onClick: () => u(e.key),
									"aria-pressed": e.key === o,
									className: z("btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 px-3.5 min-h-[48px] text-[14px] font-bold text-left", e.key === o ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"),
									children: [
										/* @__PURE__ */ (0, F.jsx)(Pr, {
											size: 16,
											className: "shrink-0"
										}),
										/* @__PURE__ */ (0, F.jsx)("span", {
											className: "break-words",
											children: e.label
										}),
										/* @__PURE__ */ (0, F.jsx)("span", {
											className: z("text-[11.5px] font-semibold", e.key === o ? "text-white/70" : "text-slate-400"),
											children: e.master ? "có master" : "chưa có master"
										})
									]
								}, e.key))
							}),
							s.length === 0 && /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[14px] text-slate-500 mt-2",
								children: [
									"Không có đối tác nào khớp “",
									t.trim(),
									"”. Hệ thống không tạo bản ghi mới để thay thế."
								]
							})
						] }), o && /* @__PURE__ */ (0, F.jsx)("button", {
							onClick: d,
							className: "btn-press touch-target mt-3 inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600",
							children: "Chọn đối tác khác"
						})]
					})
				]
			}),
			c && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: "Đang đọc ngữ cảnh đối tác…"
				})
			}),
			!c && e && e.status === "NO_PARTNER_SOURCE" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-dashed border-amber-300 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(ca, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có nguồn dữ liệu đối tác"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed",
						children: e.reason
					})
				]
			}),
			!c && e && e.status === "PARTNER_NOT_FOUND" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-amber-300 p-6 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(wi, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Không tìm thấy đối tác"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1 leading-relaxed",
						children: e.reason
					})
				]
			}),
			!c && (!e || e.status === "NO_SELECTION") && a.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(Si, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Bảng ngữ cảnh đang trống"
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Chọn một đối tác ở trên để xem hồ sơ pháp lý, lô liên kết và công nợ thật."
					})
				]
			}),
			l && e && /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex items-start gap-2 flex-wrap",
							children: [/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "min-w-0",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[11.5px] font-extrabold uppercase tracking-wider text-[#1e5aa8]",
										children: "Hồ sơ pháp lý · danh tính"
									}),
									/* @__PURE__ */ (0, F.jsx)("h2", {
										className: "text-[19px] md:text-[21px] font-extrabold text-[#0f2a4a] break-words mt-0.5",
										children: V(f?.displayName)
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[13px] text-slate-500 mt-0.5 break-all",
										children: [
											"Mã: ",
											V(f?.displayId),
											" · ",
											(e.matchedSources ?? []).join(" · ") || "—"
										]
									})
								]
							}), /* @__PURE__ */ (0, F.jsx)("span", {
								className: "ml-auto shrink-0 flex items-center gap-1.5",
								children: /* @__PURE__ */ (0, F.jsxs)(H, {
									tone: qo(f?.masterStatus),
									size: "sm",
									children: ["master: ", f?.masterStatus === "KNOWN" ? "CÓ HỒ SƠ" : "CHƯA CÓ"]
								})
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2 break-words",
							children: [
								"Nguồn danh tính: ",
								V(f?.masterSource),
								f?.contextName ? ` · ngữ cảnh lô ghi nhận: ${f.contextName}${f.contextId ? ` (${f.contextId})` : ""}` : ""
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)(Jo, {
									label: "Mã số thuế / pháp lý",
									value: p?.legalCode,
									mono: !0
								}),
								/* @__PURE__ */ (0, F.jsx)(Jo, {
									label: "Điện thoại",
									value: p?.phone,
									mono: !0
								}),
								/* @__PURE__ */ (0, F.jsx)(Jo, {
									label: "Email",
									value: p?.email
								}),
								/* @__PURE__ */ (0, F.jsx)(Jo, {
									label: "Người đại diện",
									value: p ? `${p.representative}${p.representativeTitle ? ` — ${p.representativeTitle}` : ""}` : null
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border border-slate-200 p-3 sm:col-span-2 lg:col-span-2",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
										children: "Địa chỉ pháp lý"
									}), /* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-0.5 font-semibold text-[14.5px] break-words",
										children: V(p?.legalAddress)
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "mt-3 rounded-xl border-2 border-slate-100 bg-slate-50/60 p-3",
							children: [/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-slate-500",
								children: "Tài khoản thanh toán (nguyên văn từ master)"
							}), /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "grid gap-2 mt-2 sm:grid-cols-2 lg:grid-cols-4",
								children: [
									/* @__PURE__ */ (0, F.jsx)(Jo, {
										label: "Chủ tài khoản",
										value: p?.bankAccountHolder
									}),
									/* @__PURE__ */ (0, F.jsx)(Jo, {
										label: "Số tài khoản",
										value: p?.bankAccountNumber,
										mono: !0
									}),
									/* @__PURE__ */ (0, F.jsx)(Jo, {
										label: "Ngân hàng",
										value: p?.bankName
									}),
									/* @__PURE__ */ (0, F.jsx)(Jo, {
										label: "Chi nhánh",
										value: p?.bankBranch
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2 mt-3",
							children: [/* @__PURE__ */ (0, F.jsxs)("span", {
								className: "text-[12.5px] font-bold text-slate-500 inline-flex items-center gap-1.5",
								children: [/* @__PURE__ */ (0, F.jsx)(Zi, { size: 14 }), " Vai trò theo lô:"]
							}), (e.roles ?? []).length === 0 ? /* @__PURE__ */ (0, F.jsx)("span", {
								className: "text-[13.5px] font-semibold text-slate-400",
								children: "—"
							}) : (e.roles ?? []).map((e) => /* @__PURE__ */ (0, F.jsx)("span", {
								className: "rounded-full bg-slate-100 px-3 py-1 text-[12.5px] font-bold text-slate-600",
								children: e
							}, e))]
						})
					]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(vr, { size: 18 }),
						title: `Lô hàng liên kết · ${e.shipmentCount ?? 0}`,
						sub: "Mã lô lấy từ chính dữ liệu; chi tiết lô không bị lặp lại ở đây — bấm Mở lô để sang màn hình Lô hàng."
					}), g.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-2",
						children: [
							"Chưa có lô nào liên kết với đối tác này trong dữ liệu hiện tại — ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
							", không phải 0 lô."
						]
					}) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "hidden lg:block mt-3 overflow-x-auto",
							children: /* @__PURE__ */ (0, F.jsxs)("table", {
								className: "tbl w-full text-[14px] min-w-[900px]",
								children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Lô" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Vai trò" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Tuyến" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Khách cần giao" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Kế hoạch" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Trạng thái" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Chú ý" }),
									/* @__PURE__ */ (0, F.jsx)("th", { children: "Hành động" })
								] }) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: g.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
									className: "hover:bg-slate-50",
									children: [
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "font-extrabold text-[#1e5aa8] whitespace-nowrap",
											children: e.shipmentId
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: V(e.role) }),
										/* @__PURE__ */ (0, F.jsx)("td", { children: V(e.route) }),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "whitespace-nowrap",
											children: V(e.requiredDate)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "whitespace-nowrap",
											children: V(e.plannedDate)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: V(e.status) }),
										/* @__PURE__ */ (0, F.jsx)("td", {
											className: "max-w-[220px] text-[13px]",
											children: V(e.attention)
										}),
										/* @__PURE__ */ (0, F.jsx)("td", { children: e.canOpen ? /* @__PURE__ */ (0, F.jsxs)(P, {
											to: e.openHref,
											className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
											children: [/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }), " Mở lô"]
										}) : /* @__PURE__ */ (0, F.jsxs)("span", {
											className: "inline-flex items-center gap-1 text-[12.5px] font-bold text-slate-400",
											children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 13 }), " không mở được"]
										}) })
									]
								}, e.shipmentId)) })]
							})
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "lg:hidden space-y-3 mt-3",
							children: g.map((e) => /* @__PURE__ */ (0, F.jsx)(Xo, { row: e }, e.shipmentId))
						}),
						e.shipmentTruncated && /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[12.5px] text-amber-700 font-semibold mt-2",
							children: [
								"Danh sách rút gọn — còn ",
								Math.max(0, (e.shipmentCount ?? 0) - g.length),
								" lô khác chưa hiển thị."
							]
						})
					] })]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, F.jsx)(U, {
							icon: /* @__PURE__ */ (0, F.jsx)(Oa, {
								size: 18,
								className: "text-[#1e5aa8]"
							}),
							title: "Công nợ phải trả theo lô",
							sub: m?.note ?? "",
							right: /* @__PURE__ */ (0, F.jsx)(H, {
								tone: qo(m?.status),
								size: "sm",
								children: V(m?.statusLabel)
							})
						}),
						h.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "text-[14px] text-slate-500 mt-2",
							children: [
								"Chưa có nghĩa vụ/thanh toán canonical nào cho đối tác này. Phải trả: ",
								/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
								" — hệ thống không hiển thị 0."
							]
						}) : /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "space-y-2.5 mt-3",
							children: [h.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
								className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3",
								children: [
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "flex items-center gap-2 flex-wrap",
										children: [
											e.shipmentId && y.has(e.shipmentId.toLowerCase()) ? /* @__PURE__ */ (0, F.jsx)(P, {
												to: `/lo-hang/${e.shipmentId}?tab=tai-chinh`,
												className: "font-extrabold text-[15.5px] text-[#1e5aa8] hover:underline break-all",
												children: e.shipmentId
											}) : /* @__PURE__ */ (0, F.jsx)("span", {
												className: "font-extrabold text-[15.5px] text-[#0f2a4a] break-all",
												children: V(e.shipmentId)
											}),
											/* @__PURE__ */ (0, F.jsx)("span", {
												className: "rounded-md bg-white border px-2 py-0.5 text-[12px] font-bold",
												children: V(e.currency)
											}),
											/* @__PURE__ */ (0, F.jsx)(H, {
												tone: qo(e.status),
												size: "sm",
												children: V(e.status)
											}),
											/* @__PURE__ */ (0, F.jsxs)("span", {
												className: "ml-auto text-[11.5px] text-slate-400",
												children: [e.obligationIds.length, " nghĩa vụ"]
											})
										]
									}),
									/* @__PURE__ */ (0, F.jsxs)("div", {
										className: "grid grid-cols-3 gap-2 mt-2",
										children: [
											/* @__PURE__ */ (0, F.jsx)(Yo, {
												label: "Phải trả",
												value: e.payable,
												ccy: e.currency
											}),
											/* @__PURE__ */ (0, F.jsx)(Yo, {
												label: "Đã trả",
												value: e.paid,
												ccy: e.currency
											}),
											/* @__PURE__ */ (0, F.jsx)(Yo, {
												label: "Còn lại",
												value: e.remaining,
												ccy: e.currency,
												strong: !0
											})
										]
									}),
									/* @__PURE__ */ (0, F.jsxs)("p", {
										className: "text-[11.5px] text-slate-400 mt-1.5 break-words",
										children: ["nguồn: ", V(e.source)]
									})
								]
							}, e.id ?? `${e.shipmentId}-${e.currency}-${t}`)), /* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12.5px] text-slate-500",
								children: [Object.entries(m?.byCurrency ?? {}).map(([e, t]) => `${e}: ${t.rowCount} dòng · ${t.shipmentIds.length} lô`).join(" · ") || "—", " — không cộng gộp khác loại tiền tệ, không tổng hợp công nợ toàn đối tác tại đây."]
							})]
						}),
						/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "flex flex-wrap gap-2.5 mt-3",
							children: [/* @__PURE__ */ (0, F.jsxs)(P, {
								to: m?.worklistHref ?? "/tai-chinh/cong-no-doi-tac",
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[48px]",
								children: ["Mở Công nợ đối tác ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 16 })]
							}), /* @__PURE__ */ (0, F.jsx)(P, {
								to: "/lo-hang",
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[48px]",
								children: "Xem Lô Hàng"
							})]
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: "Số liệu do sổ cái canonical dẫn xuất (C2B/C2D); màn hình này chỉ đọc lại, không tự tính."
						})
					]
				}),
				v.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(wi, { size: 18 }),
						title: `Tài liệu bằng chứng theo lô · ${v.length}`,
						sub: "Dự phóng từ hồ sơ lô hiện có — không có kho tài liệu riêng của đối tác."
					}), /* @__PURE__ */ (0, F.jsx)("div", {
						className: "grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3",
						children: v.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a] break-all",
									children: V(e.document)
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[12.5px] text-slate-500 mt-0.5 break-all",
									children: [
										V(e.shipmentId),
										" · ",
										V(e.status)
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[11.5px] text-slate-400 mt-1 break-words",
									children: ["nguồn: ", V(e.source)]
								})
							]
						}, `${e.shipmentId}-${e.document}-${t}`))
					})]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "grid gap-3 lg:grid-cols-2",
					children: [/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-amber-700",
								children: "Context còn thiếu / chưa xác định"
							}),
							/* @__PURE__ */ (0, F.jsxs)("ul", {
								className: "mt-2 space-y-1.5",
								children: [b.map((e) => /* @__PURE__ */ (0, F.jsxs)("li", {
									className: "text-[13.5px] text-slate-600 flex items-start gap-2",
									children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
										size: 15,
										className: "shrink-0 mt-0.5 text-amber-600"
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "break-words",
										children: e
									})]
								}, e)), b.length === 0 && /* @__PURE__ */ (0, F.jsx)("li", {
									className: "text-[13.5px] text-slate-500",
									children: "Không có missing field nào trong dữ liệu hiện có."
								})]
							}),
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[12px] text-slate-400 mt-2.5",
								children: [
									"Trường thiếu hiển thị “",
									"—",
									"” — hệ thống không điền 0 và không suy đoán."
								]
							})
						]
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-slate-500",
								children: "Context không khả dụng trong hệ thống"
							}),
							/* @__PURE__ */ (0, F.jsx)("ul", {
								className: "mt-2 space-y-1.5",
								children: x.map((e) => /* @__PURE__ */ (0, F.jsxs)("li", {
									className: "text-[13.5px] text-slate-600 flex items-start gap-2",
									children: [/* @__PURE__ */ (0, F.jsx)(Li, {
										size: 14,
										className: "shrink-0 mt-1 text-slate-400"
									}), /* @__PURE__ */ (0, F.jsx)("span", {
										className: "break-words",
										children: e
									})]
								}, e))
							}),
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12px] text-slate-400 mt-2.5",
								children: "Đây là chủ đích: màn hình không dựng tab/score/activity cho dữ liệu backend chưa tồn tại."
							})
						]
					})]
				})
			] })
		]
	});
}
//#endregion
//#region src/pages/Reconciliation.tsx
var Qo = {
	obligation: "Phải trả / nghĩa vụ",
	money: "Tiền đã phát sinh"
}, $o = {
	MATCHED: "green",
	ALLOCATED: "green",
	PARTIAL: "amber",
	UNMATCHED: "red",
	UNALLOCATED: "red"
};
function es(e) {
	let t = [{
		value: "ALL",
		label: "Tất cả"
	}], n = [{
		value: "REVIEW",
		label: "Cần rà soát"
	}];
	return e === "obligation" ? [
		...t,
		{
			value: "MATCHED",
			label: "Đã đối soát đủ"
		},
		{
			value: "PARTIAL",
			label: "Một phần"
		},
		{
			value: "UNMATCHED",
			label: "Chưa đối soát"
		},
		...n
	] : e === "money" ? [
		...t,
		{
			value: "ALLOCATED",
			label: "Đã phân bổ hết"
		},
		{
			value: "PARTIAL",
			label: "Một phần"
		},
		{
			value: "UNALLOCATED",
			label: "Chưa phân bổ"
		},
		...n
	] : [
		...t,
		{
			value: "MATCHED",
			label: "Đã đối soát đủ"
		},
		{
			value: "ALLOCATED",
			label: "Đã phân bổ hết"
		},
		{
			value: "PARTIAL",
			label: "Một phần"
		},
		{
			value: "UNMATCHED",
			label: "Chưa đối soát"
		},
		{
			value: "UNALLOCATED",
			label: "Chưa phân bổ"
		},
		...n
	];
}
var ts = [
	{
		value: "ALL",
		label: "Cả hai"
	},
	{
		value: "obligation",
		label: "Nghĩa vụ"
	},
	{
		value: "money",
		label: "Tiền"
	}
];
function ns(e) {
	return [
		`q=${(e.query ?? "").trim().toLowerCase()}`,
		`c=${(e.currency ?? "ALL").trim().toUpperCase()}`,
		`s=${(e.state ?? "ALL").trim().toUpperCase()}`,
		`d=${(e.side ?? "ALL").trim().toUpperCase()}`
	].join("|");
}
function rs({ value: e, ccy: t, strong: n }) {
	return /* @__PURE__ */ (0, F.jsx)("span", {
		className: z("tabular-nums whitespace-nowrap", n ? "font-extrabold text-[#0f2a4a]" : "font-bold"),
		children: Ba(e) ? `— ${t}`.trim() : B(e, t)
	});
}
function is({ row: e }) {
	return e.matchState ? /* @__PURE__ */ (0, F.jsx)(H, {
		tone: $o[e.matchState] ?? "gray",
		size: "sm",
		children: e.matchLabel ?? e.matchState
	}) : /* @__PURE__ */ (0, F.jsxs)(H, {
		tone: "gray",
		size: "sm",
		children: ["trạng thái ", "—"]
	});
}
function as({ row: e }) {
	let t = [
		e.obligationIds.length ? `nghĩa vụ: ${e.obligationIds.join(", ")}` : null,
		e.transactionIds.length ? `giao dịch: ${e.transactionIds.join(", ")}` : null,
		e.allocationIds.length ? `phân bổ: ${e.allocationIds.join(", ")}` : null
	].filter(Boolean);
	return /* @__PURE__ */ (0, F.jsx)("p", {
		className: "text-[12px] text-slate-500 break-words leading-relaxed",
		children: t.length ? t.join(" · ") : "Chưa có tham chiếu phân bổ — —"
	});
}
function os({ row: e }) {
	return e.canOpen ? /* @__PURE__ */ (0, F.jsxs)(P, {
		to: e.openHref,
		className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13px] px-3.5 min-h-[44px]",
		children: [
			/* @__PURE__ */ (0, F.jsx)(fi, { size: 15 }),
			" Mở lô ",
			e.shipmentId
		]
	}) : /* @__PURE__ */ (0, F.jsxs)("span", {
		className: "touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13px] px-3.5 min-h-[44px]",
		children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 14 }), " Lô không có trong dữ liệu"]
	});
}
function ss({ row: e }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "rounded-2xl bg-white border border-slate-200 p-4",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex items-center gap-2 flex-wrap",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "font-extrabold text-[16px] text-[#0f2a4a] break-all",
						children: e.shipmentId
					}),
					/* @__PURE__ */ (0, F.jsx)(is, { row: e }),
					/* @__PURE__ */ (0, F.jsx)(H, {
						tone: e.side === "obligation" ? "blue" : "gray",
						size: "sm",
						children: Qo[e.side] ?? e.side
					}),
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
						children: e.currency
					}),
					e.reviewReason ? /* @__PURE__ */ (0, F.jsx)(H, {
						tone: "amber",
						size: "sm",
						children: "cần rà soát"
					}) : null
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "text-[13.5px] text-slate-600 mt-1.5 break-words",
				children: [V(e.partnerName), e.purpose ? ` · ${V(e.purpose)}` : ""]
			}),
			e.occurredAt ? /* @__PURE__ */ (0, F.jsxs)("p", {
				className: "text-[12.5px] text-slate-500 mt-0.5",
				children: ["Phát sinh: ", e.occurredAt]
			}) : null,
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "grid grid-cols-3 gap-2 mt-3",
				children: [
					{
						label: e.side === "obligation" ? "Phải trả" : "Số tiền",
						value: e.amount
					},
					{
						label: "Đã phân bổ",
						value: e.allocated
					},
					{
						label: e.side === "obligation" ? "Còn lại" : "Chưa phân bổ",
						value: e.remaining
					}
				].map((t) => /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-xl bg-slate-50 border border-slate-200 p-2 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
						children: t.label
					}), /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[13px] mt-0.5",
						children: /* @__PURE__ */ (0, F.jsx)(rs, {
							value: t.value,
							ccy: e.currency
						})
					})]
				}, t.label))
			}),
			e.reviewReason ? /* @__PURE__ */ (0, F.jsxs)("p", {
				className: "text-[13px] mt-2.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800",
				children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
					size: 15,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, F.jsx)("span", { children: e.reviewReason })]
			}) : null,
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "mt-3",
				children: /* @__PURE__ */ (0, F.jsx)(as, { row: e })
			}),
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "mt-3",
				children: /* @__PURE__ */ (0, F.jsx)(os, { row: e })
			})
		]
	});
}
function cs({ options: e, value: t, onPick: n, ariaLabel: r }) {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "flex flex-wrap gap-2",
		role: "group",
		"aria-label": r,
		children: e.map((e) => /* @__PURE__ */ (0, F.jsx)("button", {
			onClick: () => n(e.value),
			"aria-pressed": e.value === t,
			className: z("btn-press touch-target rounded-xl border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold", e.value === t ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"),
			children: e.label
		}, e.value))
	});
}
function ls() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.reconciliation ?? null, [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(null), a = e?.rows ?? [], o = e?.totals ?? {}, s = e?.currencies ?? [], c = e?.side ?? "ALL", l = e?.state ?? "ALL", u = e?.currency ?? "ALL", d = (0, _.useMemo)(() => a.filter((e) => e.reviewReason), [a]), f = (e) => {
		let n = {
			query: e.query ?? t,
			currency: e.currency ?? u,
			state: e.state ?? l,
			side: e.side ?? c
		};
		e.side && e.side !== c && !e.state && (n.state = "ALL"), i(ns(n)), te("reconciliation_filter", n);
	}, p = () => {
		n("");
		let e = {
			query: "",
			currency: "ALL",
			state: "ALL",
			side: "ALL"
		};
		i(ns(e)), te("reconciliation_filter", e);
	}, m = e ? ns({
		query: e.query,
		currency: e.currency,
		state: e.state,
		side: e.side
	}) : null, h = r !== null && m !== null && r !== m, g = !(!e || !e.query && e.currency === "ALL" && e.state === "ALL" && e.side === "ALL");
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(ta, {
							size: 20,
							className: "text-white"
						}),
						title: "Đối soát",
						sub: "Nghĩa vụ đã được phân bổ tới đâu, và khoản tiền nào chưa được phân bổ — đọc từ ledger canonical. Màn hình chỉ đọc, không ghi, không sửa số dư.",
						right: /* @__PURE__ */ (0, F.jsxs)("span", {
							className: "hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-[12px] font-bold text-slate-600",
							children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 13 }), " CHỈ ĐỌC"]
						})
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [
							/* @__PURE__ */ (0, F.jsx)(R, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}),
							/* @__PURE__ */ (0, F.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								onKeyDown: (e) => {
									e.key === "Enter" && f({ query: t });
								},
								placeholder: "Tìm theo mã lô, mã nghĩa vụ, mã giao dịch, phân bổ hoặc tên đối tác…",
								"aria-label": "Tìm trong đối soát",
								className: "w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
							}),
							/* @__PURE__ */ (0, F.jsx)("button", {
								onClick: () => f({ query: t }),
								className: "btn-press touch-target shrink-0 mr-2 rounded-lg bg-[#1e5aa8] text-white font-bold text-[13.5px] px-3.5 min-h-[40px]",
								children: "Tìm"
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, F.jsx)(cs, {
								ariaLabel: "Lọc theo loại dòng",
								options: ts,
								value: c,
								onPick: (e) => f({ side: e })
							}),
							/* @__PURE__ */ (0, F.jsx)(cs, {
								ariaLabel: "Lọc theo trạng thái đối soát",
								options: es(c),
								value: es(c).some((e) => e.value === l) ? l : "ALL",
								onPick: (e) => f({ state: e })
							}),
							/* @__PURE__ */ (0, F.jsx)(cs, {
								ariaLabel: "Lọc theo tiền tệ",
								options: [{
									value: "ALL",
									label: "Mọi tiền tệ"
								}, ...s.map((e) => ({
									value: e,
									label: e
								}))],
								value: u,
								onPick: (e) => f({ currency: e })
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-wrap items-center gap-x-3 gap-y-1 mt-3",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									"Hiển thị ",
									/* @__PURE__ */ (0, F.jsx)("b", { children: e?.visibleCount ?? 0 }),
									" / ",
									e?.totalCount ?? 0,
									" dòng",
									e?.truncated ? ` (giới hạn ${e?.maxRows})` : ""
								]
							}),
							g ? /* @__PURE__ */ (0, F.jsx)("p", {
								className: "text-[12.5px] text-slate-400",
								children: "Bộ lọc chỉ thu hẹp danh sách — tổng theo tiền tệ ở dưới vẫn là toàn bộ ledger."
							}) : null,
							g ? /* @__PURE__ */ (0, F.jsxs)("button", {
								onClick: p,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600",
								children: [/* @__PURE__ */ (0, F.jsx)(wr, { size: 15 }), " Bỏ lọc"]
							}) : null
						]
					})
				]
			}),
			h && /* @__PURE__ */ (0, F.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: "Đang đọc ledger canonical…"
				})
			}),
			e && e.status === "NO_SOURCE" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-dashed border-red-300 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-red-50 text-red-600 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(Wr, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa đọc được ledger canonical"
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed",
						children: [
							e.error ?? "Không có kết nối tới cơ sở dữ liệu.",
							" Hệ thống không tự tạo số liệu thay thế: trạng thái là ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
							", không phải 0."
						]
					})
				]
			}),
			e && e.status === "EMPTY" && /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, F.jsx)(ta, { size: 26 })
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có bản ghi đối soát"
					}),
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[620px] mx-auto leading-relaxed",
						children: [
							"Chưa có nghĩa vụ hay giao dịch canonical nào gắn với lô hàng. Đây là trạng thái",
							/* @__PURE__ */ (0, F.jsx)("b", { children: " chưa có dữ liệu" }),
							", không phải công nợ bằng 0."
						]
					})
				]
			}),
			e && e.status !== "EMPTY" && e.status !== "NO_SOURCE" && /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [
				s.length > 0 && /* @__PURE__ */ (0, F.jsx)("div", {
					className: "grid gap-3 md:grid-cols-2",
					children: s.map((e) => {
						let t = o[e];
						if (!t) return null;
						let n = t.states ?? {};
						return /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl bg-white border border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "flex items-center gap-2 flex-wrap",
									children: [
										/* @__PURE__ */ (0, F.jsx)("h3", {
											className: "text-[16px] font-extrabold text-[#0f2a4a]",
											children: e
										}),
										e === "UNKNOWN" ? /* @__PURE__ */ (0, F.jsx)(H, {
											tone: "gray",
											size: "sm",
											children: "chưa rõ tiền tệ"
										}) : null,
										t.review.count > 0 ? /* @__PURE__ */ (0, F.jsxs)(H, {
											tone: "amber",
											size: "sm",
											children: [t.review.count, " dòng cần rà soát"]
										}) : null
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[12px] text-slate-400 mt-0.5",
									children: [
										t.obligations.count,
										" nghĩa vụ · ",
										t.money.count,
										" giao dịch"
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "grid grid-cols-3 gap-2 mt-3",
									children: [
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
												children: "Phải trả"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, F.jsx)(rs, {
													value: t.obligations.amount,
													ccy: e
												})
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
												children: "Đã phân bổ"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, F.jsx)(rs, {
													value: t.obligations.allocated,
													ccy: e
												})
											})]
										}),
										/* @__PURE__ */ (0, F.jsxs)("div", {
											className: "rounded-xl bg-amber-50 border border-amber-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-amber-700",
												children: "Còn lại"
											}), /* @__PURE__ */ (0, F.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, F.jsx)(rs, {
													value: t.obligations.remaining,
													ccy: e,
													strong: !0
												})
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[12.5px] text-slate-500 mt-2.5",
									children: ["Tiền chưa phân bổ: ", /* @__PURE__ */ (0, F.jsx)(rs, {
										value: t.money.unallocated,
										ccy: e
									})]
								}),
								/* @__PURE__ */ (0, F.jsx)("div", {
									className: "flex flex-wrap gap-1.5 mt-2.5",
									children: Object.entries(n).filter(([, e]) => e > 0).map(([e, t]) => /* @__PURE__ */ (0, F.jsxs)("span", {
										className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600",
										children: [
											e,
											": ",
											t
										]
									}, e))
								}),
								t.review.count > 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
									className: "text-[12.5px] mt-2 text-amber-800",
									children: ["Trong đó cần rà soát: ", /* @__PURE__ */ (0, F.jsx)(rs, {
										value: t.review.amount,
										ccy: e
									})]
								}) : null
							]
						}, e);
					})
				}),
				d.length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-amber-50 border-2 border-amber-200 p-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "inline-flex items-center gap-1.5 text-[14px] font-extrabold text-amber-900",
							children: [
								/* @__PURE__ */ (0, F.jsx)(Wr, { size: 16 }),
								" ",
								d.length,
								" dòng cần rà soát"
							]
						}),
						/* @__PURE__ */ (0, F.jsx)("ul", {
							className: "mt-2 space-y-1",
							children: d.slice(0, 8).map((e) => /* @__PURE__ */ (0, F.jsxs)("li", {
								className: "text-[13px] text-amber-900 break-words",
								children: [
									/* @__PURE__ */ (0, F.jsx)("b", { children: e.shipmentId }),
									" · ",
									V(e.partnerName),
									" · ",
									e.currency,
									" — ",
									e.reviewReason
								]
							}, e.id))
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[12.5px] text-amber-800 mt-2",
							children: "Dòng cần rà soát vẫn được cộng trong tổng của tiền tệ đó và được nêu riêng ở đây — không bị ẩn, cũng không tự động coi là đã đối soát."
						})
					]
				}),
				a.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-8 text-center",
					children: [/* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[15px] font-extrabold text-[#0f2a4a]",
						children: "Không có dòng nào khớp bộ lọc"
					}), /* @__PURE__ */ (0, F.jsx)("p", {
						className: "text-[13.5px] text-slate-500 mt-1",
						children: "Tổng theo tiền tệ ở trên vẫn là toàn bộ ledger — bộ lọc không làm thay đổi số tổng."
					})]
				}) : /* @__PURE__ */ (0, F.jsxs)(F.Fragment, { children: [/* @__PURE__ */ (0, F.jsx)("div", {
					className: "space-y-3 md:hidden",
					children: a.map((e) => /* @__PURE__ */ (0, F.jsx)(ss, { row: e }, e.id))
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: /* @__PURE__ */ (0, F.jsxs)("table", {
						className: "w-full text-[13.5px]",
						children: [/* @__PURE__ */ (0, F.jsx)("thead", {
							className: "bg-slate-50 text-slate-500",
							children: /* @__PURE__ */ (0, F.jsx)("tr", { children: [
								"Lô hàng",
								"Đối tác",
								"Loại",
								"Trạng thái",
								"Số tiền",
								"Đã phân bổ",
								"Còn lại",
								"Tiền tệ",
								"Thao tác"
							].map((e) => /* @__PURE__ */ (0, F.jsx)("th", {
								className: "text-left font-bold text-[11.5px] uppercase tracking-wide px-3 py-2.5",
								children: e
							}, e)) })
						}), /* @__PURE__ */ (0, F.jsx)("tbody", { children: a.map((e) => /* @__PURE__ */ (0, F.jsxs)("tr", {
							className: "border-t border-slate-100 align-top",
							children: [
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "px-3 py-2.5",
									children: [/* @__PURE__ */ (0, F.jsx)("p", {
										className: "font-extrabold text-[#0f2a4a] break-all",
										children: e.shipmentId
									}), /* @__PURE__ */ (0, F.jsx)(as, { row: e })]
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "px-3 py-2.5 break-words",
									children: [
										/* @__PURE__ */ (0, F.jsx)("p", {
											className: "font-semibold",
											children: V(e.partnerName)
										}),
										e.purpose ? /* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-slate-500",
											children: e.purpose
										}) : null,
										e.occurredAt ? /* @__PURE__ */ (0, F.jsx)("p", {
											className: "text-[12px] text-slate-500",
											children: e.occurredAt
										}) : null
									]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5 whitespace-nowrap",
									children: Qo[e.side] ?? e.side
								}),
								/* @__PURE__ */ (0, F.jsxs)("td", {
									className: "px-3 py-2.5",
									children: [/* @__PURE__ */ (0, F.jsx)(is, { row: e }), e.reviewReason ? /* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] text-amber-800 mt-1 break-words",
										children: e.reviewReason
									}) : null]
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, F.jsx)(rs, {
										value: e.amount,
										ccy: e.currency
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, F.jsx)(rs, {
										value: e.allocated,
										ccy: e.currency
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, F.jsx)(rs, {
										value: e.remaining,
										ccy: e.currency,
										strong: !0
									})
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5 whitespace-nowrap font-bold",
									children: e.currency
								}),
								/* @__PURE__ */ (0, F.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, F.jsx)(os, { row: e })
								})
							]
						}, e.id)) })]
					})
				})] }),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, F.jsx)(Oa, { size: 15 }), " Ghi nhận ở đâu"]
						}),
						/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-1",
							children: "Bàn đối soát không ghi. Ghi nhận phải trả, thanh toán đối tác và thu tiền khách vẫn đi qua writer canonical có RBAC, audit và idempotency riêng."
						}),
						/* @__PURE__ */ (0, F.jsx)("div", {
							className: "flex flex-wrap gap-2 mt-3",
							children: (e.actions ?? []).map((e) => /* @__PURE__ */ (0, F.jsxs)(P, {
								to: e.href,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8] text-[#1e5aa8] font-bold text-[13.5px] px-3.5 min-h-[44px]",
								children: [
									/* @__PURE__ */ (0, F.jsx)(br, { size: 15 }),
									" ",
									e.label
								]
							}, e.href))
						})
					]
				}),
				(e.unavailable ?? []).length > 0 && /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl bg-slate-50 border border-slate-200 p-4",
					children: [/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [/* @__PURE__ */ (0, F.jsx)(wi, { size: 15 }), " Ngoài phạm vi bàn này"]
					}), /* @__PURE__ */ (0, F.jsx)("ul", {
						className: "mt-2 space-y-1",
						children: (e.unavailable ?? []).map((e) => /* @__PURE__ */ (0, F.jsxs)("li", {
							className: "text-[13px] text-slate-600 break-words",
							children: ["· ", e]
						}, e))
					})]
				})
			] })
		]
	});
}
//#endregion
//#region src/pages/CeoReport.tsx
function us({ position: e, kind: t }) {
	let n = t === "receivable", r = n ? "phải thu" : "phải trả", i = n ? "text-red-700" : "text-amber-800", a = n ? "bg-red-50 border-red-200" : "bg-amber-50 border-amber-200", o = e.incompleteRowCount > 0 ? "dòng còn mở đã xác định" : "dòng còn mở", s = n ? "dòng chưa đủ Finance Actual, không tính là 0" : "dòng chưa đủ số dư canonical, không tính là 0";
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		"data-testid": `ceo-${t}-${e.currency}`,
		"data-ceo-currency": e.currency,
		className: `min-w-0 rounded-2xl border p-3.5 md:p-4 ${a}`,
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex items-center justify-between gap-2",
				children: [/* @__PURE__ */ (0, F.jsx)("span", {
					className: "rounded-md bg-white/80 border border-slate-200 px-2 py-0.5 text-[12px] font-extrabold tracking-wide text-[#0f2a4a]",
					children: e.currency
				}), /* @__PURE__ */ (0, F.jsxs)("span", {
					className: "text-right text-[12px] leading-snug font-semibold text-slate-500",
					children: [
						Ka(e.openCount),
						" ",
						o
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "mt-3 text-[12.5px] font-bold uppercase tracking-wide text-slate-600",
				children: ["Còn ", r]
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: `mt-1 break-words text-[20px] leading-tight font-extrabold md:text-[23px] ${i}`,
				children: B(e.outstanding, e.currency)
			}),
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "mt-2 text-[12.5px] leading-relaxed text-slate-500",
				children: [Ka(e.rowCount), " dòng nguồn đủ điều kiện · không quy đổi sang tiền tệ khác"]
			}),
			e.incompleteRowCount > 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
				className: "mt-1 text-[12.5px] leading-relaxed font-semibold text-amber-800",
				children: [
					Ka(e.incompleteRowCount),
					" ",
					s,
					"."
				]
			}) : null
		]
	});
}
function ds({ label: e, value: t, tone: n = "gray" }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: `min-w-0 rounded-xl border px-3 py-2.5 ${{
			green: "border-emerald-200 bg-emerald-50 text-emerald-800",
			amber: "border-amber-200 bg-amber-50 text-amber-900",
			red: "border-red-200 bg-red-50 text-red-800",
			gray: "border-slate-200 bg-slate-50 text-slate-700"
		}[n]}`,
		children: [/* @__PURE__ */ (0, F.jsx)("p", {
			className: "text-[11.5px] font-bold uppercase tracking-wide opacity-75",
			children: e
		}), /* @__PURE__ */ (0, F.jsx)("p", {
			className: "mt-0.5 text-[18px] leading-tight font-extrabold",
			children: Ka(t)
		})]
	});
}
function fs({ children: e }) {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
		children: e
	});
}
function ps() {
	let { ceoReport: e } = Zn();
	if (!e) return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "max-w-[1000px]",
		children: /* @__PURE__ */ (0, F.jsx)(fs, { children: "Chưa nhận được tóm tắt quản trị từ nguồn Logistics. Hệ thống không hiển thị số liệu thay thế." })
	});
	let { operations: t, receivables: n, payables: r, finance: i, reconciliation: a, quickLinks: o, unavailable: s } = e, c = a.obligations, l = a.money, u = !!(a.available && c && l);
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-header",
				children: [/* @__PURE__ */ (0, F.jsx)(U, {
					icon: /* @__PURE__ */ (0, F.jsx)(Rr, { size: 20 }),
					title: "Báo cáo CEO",
					sub: "Tóm tắt vị thế hiện tại từ dữ liệu Logistics đã có. Chỉ đọc; tiền tệ luôn tách riêng.",
					right: /* @__PURE__ */ (0, F.jsx)(H, {
						tone: "blue",
						size: "sm",
						children: "CHỈ ĐỌC"
					})
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "rounded-xl border border-blue-100 bg-blue-50 px-3.5 py-2.5 text-[13.5px] leading-relaxed text-blue-900",
					children: "Dùng để nhìn nhanh vận hành, phải thu, phải trả và đối soát. Không có biểu đồ xu hướng hay số liệu ước tính."
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-operations",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(qi, { size: 20 }),
						title: "Vận hành",
						sub: "Đếm từ danh sách lô hiện tại và hàng đợi việc hiện có."
					}),
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
						"data-testid": "ceo-operations-cards",
						children: [
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-3.5",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase tracking-wide text-slate-500",
										children: "Tổng lô hàng"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
										children: Ka(t.totalShipmentCount)
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[12.5px] text-slate-500",
										children: "Danh sách lô hiện tại"
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "min-w-0 rounded-2xl border border-blue-200 bg-blue-50 p-3.5",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase tracking-wide text-blue-700",
										children: "Lô đang chạy"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
										children: Ka(t.openShipmentCount)
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[12.5px] text-blue-800",
										children: "Theo định nghĩa Tổng quan"
									})
								]
							}),
							/* @__PURE__ */ (0, F.jsxs)("div", {
								className: "min-w-0 rounded-2xl border border-amber-200 bg-amber-50 p-3.5",
								children: [
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "text-[12px] font-bold uppercase tracking-wide text-amber-800",
										children: "Việc ưu tiên"
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
										children: Ka(t.actionableTaskCount)
									}),
									/* @__PURE__ */ (0, F.jsx)("p", {
										className: "mt-1 text-[12.5px] text-amber-900",
										children: "Khẩn + Cần xử lý"
									})
								]
							})
						]
					}),
					t.statusCounts.length > 0 ? /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "mt-4",
						children: [/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[12px] font-bold uppercase tracking-wide text-slate-500",
							children: "Trạng thái lô hiện tại"
						}), /* @__PURE__ */ (0, F.jsx)("div", {
							className: "mt-2 flex flex-wrap gap-2",
							"data-testid": "ceo-status-counts",
							children: t.statusCounts.map((e) => /* @__PURE__ */ (0, F.jsxs)("span", {
								className: "inline-flex max-w-full items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-semibold text-slate-700",
								children: [/* @__PURE__ */ (0, F.jsx)("span", {
									className: "truncate",
									children: e.status
								}), /* @__PURE__ */ (0, F.jsx)("b", {
									className: "text-[#0f2a4a]",
									children: Ka(e.count)
								})]
							}, e.status))
						})]
					}) : /* @__PURE__ */ (0, F.jsx)("p", {
						className: "mt-4 text-[14px] text-slate-500",
						children: "Chưa có lô hàng trong dữ liệu hiện tại."
					})
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
					"data-testid": "ceo-receivables",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(Oa, {
							size: 20,
							className: "text-emerald-600"
						}),
						title: "Phải thu khách",
						sub: "C2C · chỉ tổng từ lô đã có Finance Actual."
					}), n.positions.length > 0 ? /* @__PURE__ */ (0, F.jsx)("div", {
						className: "grid gap-3 sm:grid-cols-2",
						"data-testid": "ceo-receivable-currency-grid",
						children: n.positions.map((e) => /* @__PURE__ */ (0, F.jsx)(us, {
							position: e,
							kind: "receivable"
						}, e.currency))
					}) : /* @__PURE__ */ (0, F.jsxs)(fs, { children: [
						"Chưa có tổng phải thu đủ điều kiện từ Finance Actual. Đây là trạng thái ",
						/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa xác định" }),
						", không phải 0."
					] })]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
					"data-testid": "ceo-payables",
					children: [
						/* @__PURE__ */ (0, F.jsx)(U, {
							icon: /* @__PURE__ */ (0, F.jsx)(bi, {
								size: 20,
								className: "text-amber-700"
							}),
							title: "Phải trả đối tác",
							sub: "C2D · nghĩa vụ và phân bổ từ ledger canonical."
						}),
						r.error ? /* @__PURE__ */ (0, F.jsxs)(fs, { children: [
							"Chưa đọc được ledger phải trả canonical: ",
							r.error,
							". Hệ thống không hiển thị số 0 thay thế."
						] }) : r.hasCanonicalRecords ? /* @__PURE__ */ (0, F.jsx)("div", {
							className: "grid gap-3 sm:grid-cols-2",
							"data-testid": "ceo-payable-currency-grid",
							children: r.positions.map((e) => /* @__PURE__ */ (0, F.jsx)(us, {
								position: e,
								kind: "payable"
							}, e.currency))
						}) : /* @__PURE__ */ (0, F.jsxs)(fs, { children: [
							"Chưa có bản ghi nghĩa vụ hoặc thanh toán canonical. Đây là trạng thái ",
							/* @__PURE__ */ (0, F.jsx)("b", { children: "chưa có dữ liệu" }),
							", không phải phải trả bằng 0."
						] }),
						r.status === "REVIEW_REQUIRED" ? /* @__PURE__ */ (0, F.jsx)("p", {
							className: "mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900",
							children: "Có bản ghi phải trả cần rà soát trong desk đối soát."
						}) : null
					]
				})]
			}),
			/* @__PURE__ */ (0, F.jsx)("section", {
				className: "rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/70 p-4 md:p-5",
				"data-testid": "ceo-finance-visibility",
				children: /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex items-start gap-3",
					children: [/* @__PURE__ */ (0, F.jsx)(Wr, {
						size: 21,
						className: "mt-0.5 shrink-0 text-amber-700"
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, F.jsx)("h3", {
							className: "text-[15px] font-extrabold text-amber-950",
							children: "Khả năng nhìn thấy tài chính"
						}), i.incompleteShipmentCount > 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "mt-1 text-[13.5px] leading-relaxed text-amber-900",
							children: [Ka(i.incompleteShipmentCount), " lô chưa đủ Finance Actual. Các tổng phải thu phía trên không tính các lô này và không coi dữ liệu thiếu là 0."]
						}) : /* @__PURE__ */ (0, F.jsx)("p", {
							className: "mt-1 text-[13.5px] leading-relaxed text-amber-900",
							children: "Trang chỉ hiển thị các vị thế có nguồn hiện tại; không tự suy diễn thêm chỉ số tài chính."
						})]
					})]
				})
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-reconciliation",
				children: [
					/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(ta, {
							size: 20,
							className: "text-violet-700"
						}),
						title: "Đối soát",
						sub: "Số dòng theo trạng thái phân bổ từ ledger canonical; không phải đối soát sao kê hay sổ kế toán.",
						right: a.status === "REVIEW_REQUIRED" ? /* @__PURE__ */ (0, F.jsx)(H, {
							tone: "amber",
							size: "sm",
							children: "CẦN RÀ SOÁT"
						}) : void 0
					}),
					!a.available || !c || !l ? /* @__PURE__ */ (0, F.jsx)(fs, { children: a.status === "NO_SOURCE" ? `Chưa đọc được ledger đối soát${a.error ? `: ${a.error}` : ""}. Không hiển thị số 0 thay thế.` : "Chưa có bản ghi đối soát canonical. Đây là trạng thái chưa có dữ liệu, không phải công nợ bằng 0." }) : /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "grid gap-3 lg:grid-cols-2",
						children: [/* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5",
							"data-testid": "ceo-reconciliation-obligations",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a]",
									children: "Nghĩa vụ"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "mt-0.5 text-[12.5px] text-slate-500",
									children: "MATCHED / PARTIAL / UNMATCHED theo phân bổ đã có"
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4",
									children: [
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Đã đối soát",
											value: c.MATCHED,
											tone: "green"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Một phần",
											value: c.PARTIAL,
											tone: "amber"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Chưa đối soát",
											value: c.UNMATCHED,
											tone: "red"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Chưa xác định",
											value: c.UNKNOWN
										})
									]
								})
							]
						}), /* @__PURE__ */ (0, F.jsxs)("div", {
							className: "rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5",
							"data-testid": "ceo-reconciliation-money",
							children: [
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a]",
									children: "Giao dịch tiền"
								}),
								/* @__PURE__ */ (0, F.jsx)("p", {
									className: "mt-0.5 text-[12.5px] text-slate-500",
									children: "ALLOCATED / PARTIAL / UNALLOCATED theo phân bổ đã có"
								}),
								/* @__PURE__ */ (0, F.jsxs)("div", {
									className: "mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4",
									children: [
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Đã phân bổ",
											value: l.ALLOCATED,
											tone: "green"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Một phần",
											value: l.PARTIAL,
											tone: "amber"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Chưa phân bổ",
											value: l.UNALLOCATED,
											tone: "red"
										}),
										/* @__PURE__ */ (0, F.jsx)(ds, {
											label: "Chưa xác định",
											value: l.UNKNOWN
										})
									]
								})
							]
						})]
					}),
					u && a.reviewCount !== null && a.reviewCount > 0 ? /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900",
						children: [Ka(a.reviewCount), " dòng ledger cần rà soát."]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-quick-navigation",
				children: [/* @__PURE__ */ (0, F.jsx)(U, {
					icon: /* @__PURE__ */ (0, F.jsx)(vr, { size: 20 }),
					title: "Đi nhanh tới dữ liệu gốc",
					sub: "Mỗi liên kết mở desk đã sở hữu dữ liệu và hành động nghiệp vụ tương ứng."
				}), /* @__PURE__ */ (0, F.jsx)("div", {
					className: "grid gap-2.5 sm:grid-cols-2",
					"data-testid": "ceo-quick-links",
					children: o.map((e) => /* @__PURE__ */ (0, F.jsxs)(P, {
						to: e.href,
						className: "btn-press touch-target flex min-h-[52px] min-w-0 items-center justify-between gap-3 rounded-xl border-2 border-slate-200 bg-white px-4 py-2.5 text-left hover:border-[#1e5aa8]",
						children: [/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "min-w-0",
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: "block text-[14px] font-extrabold text-[#0f2a4a]",
								children: e.label
							}), /* @__PURE__ */ (0, F.jsx)("span", {
								className: "block truncate text-[12.5px] text-slate-500",
								children: e.note
							})]
						}), /* @__PURE__ */ (0, F.jsx)(vr, {
							size: 18,
							className: "shrink-0 text-[#1e5aa8]"
						})]
					}, e.href))
				})]
			}),
			/* @__PURE__ */ (0, F.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-slate-50 p-4",
				"data-testid": "ceo-scope-note",
				children: [/* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
					children: "Phạm vi dữ liệu"
				}), /* @__PURE__ */ (0, F.jsx)("ul", {
					className: "mt-2 space-y-1.5 text-[13.5px] leading-relaxed text-slate-600",
					children: s.map((e) => /* @__PURE__ */ (0, F.jsxs)("li", { children: ["• ", e] }, e))
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/Notebook.tsx
function ms(e, t) {
	let n = t.table ? t.table.rows.flat().join(" ") : "";
	return [
		e.label,
		t.title,
		t.summary,
		t.bullets.join(" "),
		t.tags.join(" "),
		n
	].join(" ").toLowerCase();
}
function hs(e) {
	return /^https:\/\//i.test(e.trim());
}
function gs({ provenance: e }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		"data-testid": "handbook-provenance",
		className: "rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-[12.5px] leading-relaxed text-slate-600",
		children: [
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "font-bold uppercase tracking-wide text-slate-500",
				children: "Nguồn"
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "mt-1 break-words font-mono text-[12px] text-[#0f2a4a]",
				children: e.source
			}),
			/* @__PURE__ */ (0, F.jsxs)("ul", {
				className: "mt-1 space-y-0.5",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("li", { children: [
						"Phiên bản:",
						" ",
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: "font-semibold",
							children: e.version ?? "không có trong nguồn"
						})
					] }),
					/* @__PURE__ */ (0, F.jsxs)("li", { children: [
						"Cập nhật:",
						" ",
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: "font-semibold",
							children: e.updated ?? "không có trong nguồn"
						})
					] }),
					/* @__PURE__ */ (0, F.jsxs)("li", { children: [
						"Phụ trách:",
						" ",
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: "font-semibold",
							children: e.owner ?? "không có trong nguồn"
						})
					] })
				]
			}),
			e.note ? /* @__PURE__ */ (0, F.jsx)("p", {
				className: "mt-1.5 border-t border-slate-200 pt-1.5 text-slate-500",
				children: e.note
			}) : null
		]
	});
}
function _s({ table: e }) {
	let t = e.columns.length <= 2 || e.columns.some((e) => /url|link/i.test(e)), n = (e) => t && hs(e) ? /* @__PURE__ */ (0, F.jsxs)("a", {
		href: e,
		target: "_blank",
		rel: "noreferrer",
		className: "inline-flex max-w-full items-start gap-1 break-all font-semibold text-blue-800 underline decoration-blue-300 underline-offset-2",
		children: [/* @__PURE__ */ (0, F.jsx)(ui, {
			size: 13,
			className: "mt-0.5 shrink-0"
		}), /* @__PURE__ */ (0, F.jsx)("span", {
			className: "break-all",
			children: e
		})]
	}) : /* @__PURE__ */ (0, F.jsx)("span", {
		className: "break-words",
		children: e
	});
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "mt-3",
		children: [
			/* @__PURE__ */ (0, F.jsx)("div", {
				className: "space-y-2 md:hidden",
				children: e.rows.map((t, r) => /* @__PURE__ */ (0, F.jsx)("div", {
					className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
					"data-testid": "handbook-row-mobile",
					children: t.map((t, r) => /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "py-0.5 text-[13.5px] leading-relaxed",
						children: [/* @__PURE__ */ (0, F.jsx)("span", {
							className: "mr-1.5 text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
							children: e.columns[r] ?? ""
						}), n(t)]
					}, `c-${r}`))
				}, `m-${r}`))
			}),
			/* @__PURE__ */ (0, F.jsxs)("table", {
				className: "hidden w-full border-collapse md:table",
				children: [/* @__PURE__ */ (0, F.jsx)("thead", { children: /* @__PURE__ */ (0, F.jsx)("tr", {
					className: "bg-slate-50",
					children: e.columns.map((e, t) => /* @__PURE__ */ (0, F.jsx)("th", {
						scope: "col",
						className: "border-b border-slate-200 px-2.5 py-2 text-left text-[11.5px] font-extrabold uppercase tracking-wide text-slate-500",
						children: e
					}, `h-${t}`))
				}) }), /* @__PURE__ */ (0, F.jsx)("tbody", { children: e.rows.map((e, t) => /* @__PURE__ */ (0, F.jsx)("tr", {
					className: "align-top odd:bg-white even:bg-slate-50/50",
					children: e.map((e, t) => /* @__PURE__ */ (0, F.jsx)("td", {
						className: "border-b border-slate-100 px-2.5 py-2 text-[13.5px] leading-relaxed text-slate-700",
						children: n(e)
					}, `d-${t}`))
				}, `r-${t}`)) })]
			}),
			/* @__PURE__ */ (0, F.jsxs)("p", {
				className: "mt-1.5 text-[12px] text-slate-400",
				children: [e.rows.length, " dòng · đọc từ nguồn, không phải dữ liệu mẫu"]
			})
		]
	});
}
function vs({ section: e, entry: t, onBack: n }) {
	let r = Ja[e.icon] ?? Mr;
	return /* @__PURE__ */ (0, F.jsxs)("article", {
		className: "space-y-3",
		"data-testid": "handbook-article",
		"data-article-id": t.id,
		children: [
			/* @__PURE__ */ (0, F.jsxs)("button", {
				type: "button",
				onClick: n,
				className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 bg-white px-3.5 py-2 text-[13.5px] font-bold text-[#0f2a4a]",
				"data-testid": "handbook-back",
				children: [/* @__PURE__ */ (0, F.jsx)(gr, { size: 17 }), " Về danh mục"]
			}),
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [
							/* @__PURE__ */ (0, F.jsx)(r, {
								size: 15,
								className: "shrink-0"
							}),
							" ",
							e.label
						]
					}),
					/* @__PURE__ */ (0, F.jsx)("h3", {
						className: "mt-2 break-words text-[19px] leading-snug font-extrabold text-[#0f2a4a] md:text-[21px]",
						children: t.title
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "mt-1.5 text-[14px] leading-relaxed text-slate-600",
						children: t.summary
					}),
					t.bullets.length > 0 ? /* @__PURE__ */ (0, F.jsx)("ul", {
						className: "mt-3 space-y-1.5",
						children: t.bullets.map((e, t) => /* @__PURE__ */ (0, F.jsxs)("li", {
							className: "flex gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[13.5px] leading-relaxed text-slate-700",
							children: [/* @__PURE__ */ (0, F.jsx)("span", {
								className: "mt-0.5 text-slate-400",
								children: "•"
							}), /* @__PURE__ */ (0, F.jsx)("span", {
								className: "min-w-0 break-words",
								children: e
							})]
						}, t))
					}) : null,
					t.table ? /* @__PURE__ */ (0, F.jsx)(_s, { table: t.table }) : null,
					t.tags.length > 0 ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "mt-3 flex flex-wrap gap-1.5",
						children: t.tags.map((e) => /* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600",
							children: ["#", e]
						}, e))
					}) : null,
					t.links.length > 0 ? /* @__PURE__ */ (0, F.jsx)("div", {
						className: "mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3",
						children: t.links.map((e) => /* @__PURE__ */ (0, F.jsxs)(P, {
							to: e.href,
							className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] px-3.5 py-2 text-[13.5px] font-bold text-white",
							children: [
								e.label,
								" ",
								/* @__PURE__ */ (0, F.jsx)(vr, { size: 15 })
							]
						}, e.href))
					}) : null
				]
			}),
			/* @__PURE__ */ (0, F.jsx)(gs, { provenance: t.provenance ?? e.provenance })
		]
	});
}
function ys({ section: e, entry: t, onOpen: n }) {
	return /* @__PURE__ */ (0, F.jsxs)("button", {
		type: "button",
		onClick: n,
		"data-testid": "handbook-entry",
		"data-entry-id": t.id,
		className: "btn-press w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-blue-300",
		children: [
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "flex items-start justify-between gap-3",
				children: [/* @__PURE__ */ (0, F.jsx)("h4", {
					className: "min-w-0 break-words text-[15.5px] leading-snug font-extrabold text-[#0f2a4a]",
					children: t.title
				}), /* @__PURE__ */ (0, F.jsx)(vr, {
					size: 18,
					className: "mt-0.5 shrink-0 text-slate-400"
				})]
			}),
			/* @__PURE__ */ (0, F.jsx)("p", {
				className: "mt-1.5 text-[13.5px] leading-relaxed text-slate-600",
				children: t.summary
			}),
			t.table && t.table.rows.length > 0 ? /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "mt-2 space-y-1",
				"data-testid": "handbook-preview",
				children: [t.table.rows.slice(0, 2).map((e, t) => /* @__PURE__ */ (0, F.jsx)("p", {
					className: "break-words rounded-lg bg-slate-50 px-2 py-1 font-mono text-[12px] text-slate-600",
					children: e.filter((e) => e.trim() !== "").join(" · ")
				}, t)), t.table.rows.length > 2 ? /* @__PURE__ */ (0, F.jsxs)("p", {
					className: "text-[12px] font-semibold text-slate-400",
					children: [
						"+",
						t.table.rows.length - 2,
						" dòng nữa trong bài"
					]
				}) : null]
			}) : null,
			/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "mt-2.5 flex flex-wrap items-center gap-2",
				children: [
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-600",
						children: e.label
					}),
					t.table ? /* @__PURE__ */ (0, F.jsxs)("span", {
						className: "rounded-md bg-blue-50 px-2 py-0.5 text-[11.5px] font-bold text-blue-800",
						children: [t.table.rows.length, " dòng"]
					}) : null,
					/* @__PURE__ */ (0, F.jsx)("span", {
						className: "text-[11.5px] font-semibold text-slate-400",
						children: t.tags.slice(0, 3).map((e) => `#${e}`).join(" ")
					})
				]
			})
		]
	});
}
function bs({ reason: e }) {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "max-w-[760px]",
		children: /* @__PURE__ */ (0, F.jsx)("div", {
			className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
			children: e === "pending" ? "Chưa nhận được dữ liệu Sổ tay từ backend. Trang không hiển thị nội dung mẫu thay thế." : "Nguồn tham chiếu chưa trả về mục nào có nội dung. Sổ tay hiển thị đúng trạng thái này thay vì tự soạn bài."
		})
	});
}
function xs() {
	let { handbook: e } = Zn(), [t, n] = (0, _.useState)(null), [r, i] = (0, _.useState)(null), [a, o] = (0, _.useState)(""), s = a.trim().toLowerCase(), c = (0, _.useMemo)(() => {
		let t = [];
		for (let n of e?.sections ?? []) for (let e of n.entries) t.push({
			section: n,
			entry: e,
			hay: ms(n, e)
		});
		return t;
	}, [e]), l = (0, _.useMemo)(() => {
		let e = s.length === 0 && t ? c.filter((e) => e.section.id === t) : c;
		return s ? e.filter((e) => e.hay.includes(s)) : e;
	}, [
		c,
		s,
		t
	]), u = (0, _.useMemo)(() => r ? c.find((e) => e.entry.id === r) ?? null : null, [c, r]);
	if (!e) return /* @__PURE__ */ (0, F.jsx)(bs, { reason: "pending" });
	let d = e;
	if (d.counts.entryCount === 0 && !s) return /* @__PURE__ */ (0, F.jsx)(bs, { reason: "no-source" });
	let f = d.sections.find((e) => e.id === t) ?? null, p = d.sections.filter((e) => e.state && e.entries.length === 0), m = (e) => {
		i(e), typeof window < "u" && window.scrollTo({
			top: 0,
			behavior: "auto"
		});
	}, h = () => i(null), g = (e) => {
		n(e === t ? null : e), i(null), o("");
	};
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [/* @__PURE__ */ (0, F.jsxs)("section", {
			className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
			"data-testid": "handbook-header",
			children: [
				/* @__PURE__ */ (0, F.jsx)(U, {
					icon: /* @__PURE__ */ (0, F.jsx)(Mr, { size: 20 }),
					title: "Sổ tay vận hành",
					sub: "Tra cứu quy trình, chứng từ, mã dịch vụ và phân quyền — đúng theo tài liệu hệ thống đang dùng.",
					right: /* @__PURE__ */ (0, F.jsx)(H, {
						tone: "blue",
						size: "sm",
						children: "CHỈ ĐỌC"
					})
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [
								d.counts.availableSectionCount,
								"/",
								d.counts.sectionCount,
								" mục có nội dung"
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [d.counts.entryCount, " bài tham chiếu"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							"data-testid": "handbook-note-count",
							children: [d.counts.noteTotal ?? d.counts.noteCount, " ghi chú đội ngũ"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800",
							children: [
								/* @__PURE__ */ (0, F.jsx)(oa, { size: 13 }),
								" ",
								d.readOnly ? "không sửa từ trang này" : "có chỉnh sửa"
							]
						})
					]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "relative mt-3",
					children: [
						/* @__PURE__ */ (0, F.jsx)(R, {
							size: 17,
							className: "pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
						}),
						/* @__PURE__ */ (0, F.jsx)("input", {
							type: "search",
							value: a,
							onChange: (e) => {
								o(e.target.value), i(null);
							},
							placeholder: "Tìm theo tiêu đề, nội dung, mã hoặc từ khóa…",
							"aria-label": "Tìm trong sổ tay",
							"data-testid": "handbook-search",
							className: "min-h-[48px] w-full rounded-xl border-2 border-slate-200 bg-white pl-10 pr-10 text-[15px] font-medium text-slate-800 outline-none focus:border-blue-400"
						}),
						a ? /* @__PURE__ */ (0, F.jsx)("button", {
							type: "button",
							onClick: () => o(""),
							"aria-label": "Xóa từ khóa",
							className: "touch-target absolute right-1 top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-xl text-slate-400 hover:bg-slate-100",
							children: /* @__PURE__ */ (0, F.jsx)(Aa, { size: 17 })
						}) : null
					]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "mt-3 flex flex-wrap gap-2",
					"data-testid": "handbook-categories",
					children: [/* @__PURE__ */ (0, F.jsx)("button", {
						type: "button",
						onClick: () => {
							n(null), i(null), o("");
						},
						className: z("min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors", t === null ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"),
						"data-testid": "handbook-category-all",
						children: "Tất cả"
					}), d.sections.map((e) => /* @__PURE__ */ (0, F.jsxs)("button", {
						type: "button",
						onClick: () => g(e.id),
						className: z("min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors", e.id === t ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"),
						"data-testid": `handbook-category-${e.id}`,
						children: [e.label, /* @__PURE__ */ (0, F.jsx)("span", {
							className: "ml-1.5 text-[11.5px] font-extrabold opacity-70",
							children: e.entries.length
						})]
					}, e.id))]
				})
			]
		}), u ? /* @__PURE__ */ (0, F.jsx)(vs, {
			section: u.section,
			entry: u.entry,
			onBack: h
		}) : /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]",
			children: [/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "min-w-0 space-y-2.5",
				children: [f && !s ? /* @__PURE__ */ (0, F.jsxs)("p", {
					className: "text-[13px] leading-relaxed text-slate-500",
					"data-testid": "handbook-section-lead",
					children: [
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "font-extrabold text-[#0f2a4a]",
							children: [f.label, ":"]
						}),
						" ",
						f.lead
					]
				}) : null, l.length === 0 ? /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
					"data-testid": "handbook-no-result",
					children: [
						"Không có bài nào khớp “",
						a,
						"”. Sổ tay chỉ tìm trong nội dung đã có trong nguồn và không tạo bài mới."
					]
				}) : l.map(({ section: e, entry: t }) => /* @__PURE__ */ (0, F.jsx)(ys, {
					section: e,
					entry: t,
					onOpen: () => m(t.id)
				}, `${e.id}-${t.id}`))]
			}), /* @__PURE__ */ (0, F.jsxs)("aside", {
				className: "min-w-0 space-y-3",
				children: [
					f && !s ? /* @__PURE__ */ (0, F.jsx)(gs, { provenance: f.provenance }) : null,
					p.length > 0 ? /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5",
						"data-testid": "handbook-empty-sections",
						children: [/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[12px] font-extrabold uppercase tracking-wide text-amber-800",
							children: "Mục chưa có nguồn"
						}), /* @__PURE__ */ (0, F.jsx)("ul", {
							className: "mt-1 space-y-1 text-[13px] leading-relaxed text-amber-900",
							children: p.map((e) => /* @__PURE__ */ (0, F.jsxs)("li", { children: [
								/* @__PURE__ */ (0, F.jsx)("span", {
									className: "font-bold",
									children: e.label
								}),
								" — ",
								e.state?.text
							] }, e.id))
						})]
					}) : null,
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
						children: [/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, F.jsx)(wi, { size: 14 }), " Trang này không có"]
						}), /* @__PURE__ */ (0, F.jsx)("ul", {
							className: "mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600",
							children: d.unavailable.map((e) => /* @__PURE__ */ (0, F.jsx)("li", {
								className: "break-words",
								children: e
							}, e))
						})]
					})
				]
			})]
		})]
	});
}
//#endregion
//#region src/pages/UserAccess.tsx
function Ss(e) {
	return ja[e.toUpperCase()] ?? e;
}
function Cs(e) {
	switch (e.toLowerCase()) {
		case "admin": return "red";
		case "support": return "blue";
		case "sale": return "green";
		default: return "gray";
	}
}
function ws(e) {
	return (e.trim().split(/\s+/).slice(0, 2).map((e) => [...e][0] ?? "").join("") || "?").toUpperCase();
}
function Ts({ name: e }) {
	return /* @__PURE__ */ (0, F.jsx)("span", {
		className: "break-all rounded-md bg-slate-100 px-2 py-1 font-mono text-[11.5px] font-semibold text-slate-700",
		"data-testid": "user-access-permission",
		children: e
	});
}
function Es({ account: e }) {
	let t = e.display_name || e.username;
	return /* @__PURE__ */ (0, F.jsx)("div", {
		"data-testid": "user-access-account",
		"data-username": e.username,
		"data-role": e.role,
		className: "w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5",
		children: /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex items-start gap-3",
			children: [/* @__PURE__ */ (0, F.jsx)("span", {
				className: z("grid h-10 w-10 shrink-0 place-items-center rounded-xl text-[14px] font-extrabold", e.active ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-400"),
				"aria-hidden": !0,
				children: ws(t)
			}), /* @__PURE__ */ (0, F.jsxs)("div", {
				className: "min-w-0 flex-1",
				children: [
					/* @__PURE__ */ (0, F.jsxs)("div", {
						className: "flex flex-wrap items-center gap-x-2 gap-y-1",
						children: [
							/* @__PURE__ */ (0, F.jsx)("p", {
								className: "min-w-0 break-words text-[15px] font-extrabold text-[#0f2a4a]",
								children: t
							}),
							/* @__PURE__ */ (0, F.jsx)(H, {
								tone: Cs(e.role),
								size: "sm",
								children: Ss(e.role)
							}),
							e.active ? /* @__PURE__ */ (0, F.jsxs)("span", {
								className: "inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11.5px] font-bold text-emerald-800",
								"data-testid": "user-access-account-active",
								children: [/* @__PURE__ */ (0, F.jsx)(Sr, { size: 12 }), " Hoạt động"]
							}) : /* @__PURE__ */ (0, F.jsxs)("span", {
								className: "inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-500",
								"data-testid": "user-access-account-inactive",
								children: [/* @__PURE__ */ (0, F.jsx)(Li, { size: 12 }), " Đã vô hiệu hóa"]
							})
						]
					}),
					/* @__PURE__ */ (0, F.jsx)("p", {
						className: "mt-1 break-all font-mono text-[12px] text-slate-500",
						children: e.username
					}),
					e.email ? /* @__PURE__ */ (0, F.jsx)("p", {
						className: "mt-0.5 min-w-0 break-all text-[12.5px] text-slate-500",
						children: e.email
					}) : null,
					e.user_id ? /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "mt-1 break-all font-mono text-[11px] text-slate-400",
						children: ["ID: ", e.user_id]
					}) : null
				]
			})]
		})
	});
}
function Ds({ row: e, assignable: t }) {
	return /* @__PURE__ */ (0, F.jsxs)("div", {
		"data-testid": "user-access-role-row",
		"data-role": e.role,
		className: "w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5",
		children: [/* @__PURE__ */ (0, F.jsxs)("div", {
			className: "flex flex-wrap items-center gap-2",
			children: [
				/* @__PURE__ */ (0, F.jsx)(H, {
					tone: Cs(e.role),
					size: "sm",
					children: Ss(e.role)
				}),
				e.wildcard ? /* @__PURE__ */ (0, F.jsxs)("span", {
					className: "inline-flex items-center gap-1 rounded-md bg-violet-50 px-2 py-0.5 text-[11.5px] font-bold text-violet-800",
					children: [/* @__PURE__ */ (0, F.jsx)(Ei, { size: 12 }), " * = toàn quyền"]
				}) : null,
				t ? /* @__PURE__ */ (0, F.jsx)("span", {
					className: "rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500",
					children: "vai trò gán được"
				}) : /* @__PURE__ */ (0, F.jsx)("span", {
					className: "rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700",
					children: "vai trò tương thích cũ"
				}),
				/* @__PURE__ */ (0, F.jsxs)("span", {
					className: "ml-auto text-[11.5px] font-bold text-slate-400",
					children: [e.permissionCount, " quyền"]
				})
			]
		}), /* @__PURE__ */ (0, F.jsx)("div", {
			className: "mt-2 flex flex-wrap gap-1.5",
			"data-testid": "user-access-role-permissions",
			children: e.wildcard ? /* @__PURE__ */ (0, F.jsx)("span", {
				className: "break-words text-[12.5px] leading-relaxed text-slate-500",
				children: "Toàn quyền trên mọi thao tác của hệ thống (dấu * trong ma trận nguyên bản của core.auth)."
			}) : e.permissions.map((e) => /* @__PURE__ */ (0, F.jsx)(Ts, { name: e }, e))
		})]
	});
}
function Os() {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		"data-testid": "user-access-empty",
		className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
		children: "Nguồn tài khoản của bản dựng này chưa có người dùng nào (hoặc chưa cấu hình). Trang hiển thị đúng trạng thái trống và không tự bịa tài khoản, vai trò hay quyền nào thay thế."
	});
}
function ks() {
	let e = T(), { assignableSet: t, activeCount: n } = (0, _.useMemo)(() => ({
		assignableSet: new Set(e?.roles.assignable ?? []),
		activeCount: (e?.users ?? []).filter((e) => e.active).length
	}), [e]);
	return e ? /* @__PURE__ */ (0, F.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [/* @__PURE__ */ (0, F.jsxs)("section", {
			className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
			"data-testid": "user-access-header",
			children: [
				/* @__PURE__ */ (0, F.jsx)(U, {
					icon: /* @__PURE__ */ (0, F.jsx)(Ea, { size: 20 }),
					title: "Người dùng & Vai trò",
					sub: "Xem tài khoản, vai trò và ma trận phân quyền đúng như hệ thống đang dùng — không thêm vai trò mới, không hiện dữ liệu bí mật.",
					right: /* @__PURE__ */ (0, F.jsx)(H, {
						tone: "blue",
						size: "sm",
						children: "CHỈ ĐỌC"
					})
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600",
					children: [
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							"data-testid": "user-access-authmode",
							children: e.authMode.label
						}),
						/* @__PURE__ */ (0, F.jsx)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							"data-testid": "user-access-counts",
							children: e.counts.userShown === e.counts.userCount ? `${e.counts.userCount} tài khoản` : `${e.counts.userShown}/${e.counts.userCount} tài khoản (giới hạn hiển thị)`
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [
								n,
								" hoạt động · ",
								e.counts.inactiveCount,
								" vô hiệu hóa"
							]
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [e.counts.roleCount, " vai trò trong ma trận"]
						}),
						/* @__PURE__ */ (0, F.jsxs)("span", {
							className: "inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800",
							children: [/* @__PURE__ */ (0, F.jsx)(oa, { size: 13 }), " không sửa từ trang này"]
						})
					]
				}),
				/* @__PURE__ */ (0, F.jsxs)("p", {
					"data-testid": "user-access-mode-note",
					className: z("mt-3 rounded-xl px-3 py-2.5 text-[13px] leading-relaxed", e.authMode.required ? "border border-blue-200 bg-blue-50 text-blue-900" : "border border-amber-200 bg-amber-50 text-amber-900"),
					children: [
						/* @__PURE__ */ (0, F.jsxs)("b", { children: [
							"Chế độ xác thực: ",
							e.authMode.label,
							"."
						] }),
						" ",
						e.authMode.note
					]
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					"data-testid": "user-access-current",
					className: "mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5",
					children: [/* @__PURE__ */ (0, F.jsx)(Xr, {
						size: 22,
						className: "shrink-0 text-[#1e5aa8]"
					}), /* @__PURE__ */ (0, F.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
							children: "Bạn đang đăng nhập"
						}), e.currentUser.present ? /* @__PURE__ */ (0, F.jsxs)("p", {
							className: "min-w-0 break-words text-[14px] font-extrabold text-[#0f2a4a]",
							children: [
								e.currentUser.displayName,
								" ",
								/* @__PURE__ */ (0, F.jsxs)("span", {
									className: "font-mono text-[12px] font-semibold text-slate-500",
									children: [
										"(",
										e.currentUser.username,
										")"
									]
								}),
								" ",
								"· ",
								Ss(e.currentUser.role),
								e.currentUser.wildcard ? " · toàn quyền (*)" : ` · ${e.currentUser.permissions.length} quyền`
							]
						}) : /* @__PURE__ */ (0, F.jsx)("p", {
							className: "text-[14px] font-bold text-slate-500",
							children: "Chưa xác định phiên đăng nhập"
						})]
					})]
				})
			]
		}), /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "grid gap-4 lg:grid-cols-[1fr_340px]",
			children: [/* @__PURE__ */ (0, F.jsxs)("div", {
				className: "min-w-0 space-y-4",
				children: [/* @__PURE__ */ (0, F.jsxs)("section", {
					className: "space-y-2.5",
					"data-testid": "user-access-accounts",
					children: [/* @__PURE__ */ (0, F.jsx)(U, {
						icon: /* @__PURE__ */ (0, F.jsx)(wa, { size: 18 }),
						title: "Tài khoản",
						sub: "Trường công khai chuẩn của tài khoản (tên hiển thị, tài khoản đăng nhập, vai trò, trạng thái). Không có mật khẩu hay hash."
					}), e.users.length === 0 ? /* @__PURE__ */ (0, F.jsx)(Os, {}) : e.users.map((e) => /* @__PURE__ */ (0, F.jsx)(Es, { account: e }, e.user_id || e.username))]
				}), /* @__PURE__ */ (0, F.jsxs)("section", {
					className: "space-y-2.5",
					"data-testid": "user-access-matrix",
					children: [
						/* @__PURE__ */ (0, F.jsx)(U, {
							icon: /* @__PURE__ */ (0, F.jsx)(Ei, { size: 18 }),
							title: "Ma trận phân quyền",
							sub: "Nguyên văn ROLE_PERMISSIONS của core.auth — nguồn quyền duy nhất của ứng dụng. Tên quyền giữ nguyên bản, không dịch, không thêm."
						}),
						e.permissionMatrix.map((e) => /* @__PURE__ */ (0, F.jsx)(Ds, {
							row: e,
							assignable: t.has(e.role)
						}, e.role)),
						/* @__PURE__ */ (0, F.jsxs)("p", {
							className: "break-words text-[12px] leading-relaxed text-slate-400",
							children: [
								"Nguồn: ",
								e.roles.source,
								". Vai trò gán được cho tài khoản:",
								" ",
								e.roles.assignable.map((e) => Ss(e)).join(", "),
								".",
								e.roles.legacy.length > 0 ? ` Các vai trò còn lại (${e.roles.legacy.map((e) => Ss(e)).join(", ")}) chỉ còn trong ma trận để tương thích dữ liệu cũ.` : ""
							]
						})
					]
				})]
			}), /* @__PURE__ */ (0, F.jsxs)("aside", {
				className: "min-w-0 space-y-3",
				children: [/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
					children: [/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [/* @__PURE__ */ (0, F.jsx)(wi, { size: 14 }), " Trang này không có"]
					}), /* @__PURE__ */ (0, F.jsx)("ul", {
						className: "mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600",
						"data-testid": "user-access-unavailable",
						children: e.unavailable.map((e) => /* @__PURE__ */ (0, F.jsx)("li", {
							className: "break-words",
							children: e
						}, e))
					})]
				}), /* @__PURE__ */ (0, F.jsxs)("div", {
					className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
					children: [/* @__PURE__ */ (0, F.jsxs)("p", {
						className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [/* @__PURE__ */ (0, F.jsx)(oa, { size: 14 }), " Quyền của bạn được kiểm ở đâu"]
					}), /* @__PURE__ */ (0, F.jsxs)("p", {
						className: "mt-1 text-[12.5px] leading-relaxed text-slate-600",
						children: [
							"Mọi thao tác ghi trong ứng dụng vẫn được kiểm tra bởi",
							/* @__PURE__ */ (0, F.jsx)("span", {
								className: "font-mono text-[11.5px] font-semibold",
								children: " core.auth "
							}),
							"trên máy chủ theo đúng ma trận trên. Trang này chỉ hiển thị quy tắc, không thay đổi quy tắc."
						]
					})]
				})]
			})]
		})]
	}) : /* @__PURE__ */ (0, F.jsx)("div", {
		className: "max-w-[1240px] pb-3",
		children: /* @__PURE__ */ (0, F.jsx)("div", {
			className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] text-slate-600",
			children: "Chưa có dữ liệu người dùng & phân quyền từ máy chủ. Trang chỉ đọc và không tự tạo dữ liệu thay thế."
		})
	});
}
//#endregion
//#region src/pages/PhaseB.tsx
var As = {
	"/tai-chinh/doi-soat": "Đối soát",
	"/nguoi-dung": "Người dùng & Vai trò"
};
function js() {
	let { pathname: e } = bt(), t = As[e] ?? "Màn hình phụ";
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "max-w-[680px] mx-auto mt-8",
		children: /* @__PURE__ */ (0, F.jsxs)("div", {
			className: "rounded-3xl bg-white border border-slate-200 p-8 text-center anim-slide-up",
			children: [
				/* @__PURE__ */ (0, F.jsx)("span", {
					className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
					children: /* @__PURE__ */ (0, F.jsx)(ei, { size: 26 })
				}),
				/* @__PURE__ */ (0, F.jsx)("h2", {
					className: "text-[20px] font-extrabold text-[#0f2a4a] mt-4",
					children: t
				}),
				/* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[13px] font-extrabold uppercase tracking-wide text-amber-700 mt-2",
					children: "Sắp có — chưa triển khai"
				}),
				/* @__PURE__ */ (0, F.jsx)("p", {
					className: "text-[14.5px] text-slate-500 mt-2 leading-relaxed",
					children: "Màn hình này chưa có nguồn dữ liệu nghiệp vụ chuẩn trong phiên bản hiện tại nên chưa được dựng — hệ thống không hiển thị dữ liệu mẫu thay thế. Toàn bộ phần vận hành, kinh doanh và tài chính cốt lõi — Tổng Quan, Việc Cần Xử Lý, Lô Hàng, Chi tiết lô, Tạo Lô Mới, Theo Dõi, Khách Hàng, Báo giá, Thỏa thuận, Hợp đồng, Thu tiền, Công nợ đối tác, Đối soát và Báo cáo CEO — đã chạy trên dữ liệu Logistics thật."
				}),
				/* @__PURE__ */ (0, F.jsxs)("div", {
					className: "flex flex-wrap justify-center gap-2.5 mt-5",
					children: [/* @__PURE__ */ (0, F.jsxs)(P, {
						to: "/",
						className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px]",
						children: ["Về Tổng Quan ", /* @__PURE__ */ (0, F.jsx)(vr, { size: 17 })]
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
function Ms() {
	return /* @__PURE__ */ (0, F.jsx)("div", {
		className: "min-h-[40vh] grid place-items-center",
		children: /* @__PURE__ */ (0, F.jsx)("p", {
			className: "text-[15px] font-semibold text-slate-500",
			children: "Đang tải dữ liệu vận hành…"
		})
	});
}
function Ns() {
	let e = (0, _.useSyncExternalStore)(C, S, S);
	return /* @__PURE__ */ (0, F.jsx)(Xn, { children: /* @__PURE__ */ (0, F.jsx)(qt, { children: /* @__PURE__ */ (0, F.jsx)(ro, { children: e ? /* @__PURE__ */ (0, F.jsxs)(Yt, { children: [
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/",
			element: /* @__PURE__ */ (0, F.jsx)(oo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/viec-can-xu-ly",
			element: /* @__PURE__ */ (0, F.jsx)(q, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/lo-hang",
			element: /* @__PURE__ */ (0, F.jsx)(so, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/lo-hang/:id",
			element: /* @__PURE__ */ (0, F.jsx)(lo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/tao-lo-moi",
			element: /* @__PURE__ */ (0, F.jsx)(uo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/theo-doi",
			element: /* @__PURE__ */ (0, F.jsx)(fo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/khach-hang",
			element: /* @__PURE__ */ (0, F.jsx)(_o, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/tai-chinh/thu-tien",
			element: /* @__PURE__ */ (0, F.jsx)(po, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/tai-chinh/cong-no-doi-tac",
			element: /* @__PURE__ */ (0, F.jsx)(ho, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/kinh-doanh-bao-gia",
			element: /* @__PURE__ */ (0, F.jsx)(Eo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/thoa-thuan-ban-giao",
			element: /* @__PURE__ */ (0, F.jsx)(jo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/hop-dong",
			element: /* @__PURE__ */ (0, F.jsx)(Mo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/hop-dong/moi",
			element: /* @__PURE__ */ (0, F.jsx)(Ro, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/hop-dong/:id",
			element: /* @__PURE__ */ (0, F.jsx)(Lo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/tra-cuu-thue",
			element: /* @__PURE__ */ (0, F.jsx)(Vo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/dich-thuat",
			element: /* @__PURE__ */ (0, F.jsx)(Go, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/ngu-canh-doi-tac",
			element: /* @__PURE__ */ (0, F.jsx)(Zo, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/tai-chinh/doi-soat",
			element: /* @__PURE__ */ (0, F.jsx)(ls, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/bao-cao-ceo",
			element: /* @__PURE__ */ (0, F.jsx)(ps, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/so-tay",
			element: /* @__PURE__ */ (0, F.jsx)(xs, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "/nguoi-dung",
			element: /* @__PURE__ */ (0, F.jsx)(ks, {})
		}),
		/* @__PURE__ */ (0, F.jsx)(N, {
			path: "*",
			element: /* @__PURE__ */ (0, F.jsx)(js, {})
		})
	] }) : /* @__PURE__ */ (0, F.jsx)(Ms, {}) }) }) });
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/typeof.js
function Ps(e) {
	"@babel/helpers - typeof";
	return Ps = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, Ps(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPrimitive.js
function Fs(e, t) {
	if (Ps(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (Ps(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPropertyKey.js
function Is(e) {
	var t = Fs(e, "string");
	return Ps(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/defineProperty.js
function Ls(e, t, n) {
	return (t = Is(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region src/component-entry.tsx
var Rs = class extends _.Component {
	constructor(...e) {
		super(...e), Ls(this, "state", { error: null });
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
}, zs = null, Bs = null;
function Vs(e) {
	return Bs && e.contains(Bs) ? Bs : (Bs = document.createElement("div"), Bs.className = "logi-shell", e.appendChild(Bs), Bs);
}
function Hs(e) {
	O(e.setTriggerValue ?? null);
	let t = Vs(e.parentElement);
	return zs || (zs = (0, v.createRoot)(t), zs.render(/* @__PURE__ */ (0, F.jsx)(Rs, { children: /* @__PURE__ */ (0, F.jsx)(Ns, {}) }))), e.data && typeof e.data == "object" && x(e.data), () => {
		try {
			zs?.unmount();
		} catch {}
		zs = null;
		try {
			Bs?.remove();
		} catch {}
		Bs = null, O(null);
	};
}
//#endregion
export { Hs as default };
