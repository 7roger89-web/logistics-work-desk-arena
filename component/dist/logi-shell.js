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
	var A = /\/+/g;
	function ee(e, t) {
		return typeof e == "object" && e && e.key != null ? k("" + e.key) : t.toString(36);
	}
	function j(e) {
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
	function M(e, r, i, a, o) {
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
				case d: return c = e._init, M(c(e._payload), r, i, a, o);
			}
		}
		if (c) return o = o(e), c = a === "" ? "." + ee(e, 0) : a, S(o) ? (i = "", c != null && (i = c.replace(A, "$&/") + "/"), M(o, r, i, "", function(e) {
			return e;
		})) : o != null && (O(o) && (o = D(o, i + (o.key == null || e && e.key === o.key ? "" : ("" + o.key).replace(A, "$&/") + "/") + c)), r.push(o)), 1;
		c = 0;
		var l = a === "" ? "." : a + ":";
		if (S(e)) for (var u = 0; u < e.length; u++) a = e[u], s = l + ee(a, u), c += M(a, r, i, s, o);
		else if (u = m(e), typeof u == "function") for (e = u.call(e), u = 0; !(a = e.next()).done;) a = a.value, s = l + ee(a, u++), c += M(a, r, i, s, o);
		else if (s === "object") {
			if (typeof e.then == "function") return M(j(e), r, i, a, o);
			throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		}
		return c;
	}
	function N(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return M(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function te(e) {
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
	var P = typeof reportError == "function" ? reportError : function(e) {
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
	}, F = {
		map: N,
		forEach: function(e, t, n) {
			N(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return N(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return N(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!O(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	};
	e.Activity = f, e.Children = F, e.Component = v, e.Fragment = r, e.Profiler = a, e.PureComponent = b, e.StrictMode = i, e.Suspense = l, e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = w, e.__COMPILER_RUNTIME = {
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
			_init: te
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
			i !== null && i(n, r), typeof r == "object" && r && typeof r.then == "function" && r.then(C, P);
		} catch (e) {
			P(e);
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
				t !== null && ee(x, t.startTime - e);
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
								u !== null && ee(x, u.startTime - t), i = !1;
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
		var k = new MessageChannel(), A = k.port2;
		k.port1.onmessage = D, O = function() {
			A.postMessage(null);
		};
	} else O = function() {
		_(D, 0);
	};
	function ee(t, n) {
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
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (v(C), C = -1) : h = !0, ee(x, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, S || (S = !0, O()))), r;
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
	var h = Object.assign, g = Symbol.for("react.element"), _ = Symbol.for("react.transitional.element"), v = Symbol.for("react.portal"), y = Symbol.for("react.fragment"), b = Symbol.for("react.strict_mode"), x = Symbol.for("react.profiler"), S = Symbol.for("react.consumer"), C = Symbol.for("react.context"), w = Symbol.for("react.forward_ref"), T = Symbol.for("react.suspense"), E = Symbol.for("react.suspense_list"), D = Symbol.for("react.memo"), O = Symbol.for("react.lazy"), k = Symbol.for("react.activity"), A = Symbol.for("react.memo_cache_sentinel"), ee = Symbol.iterator;
	function j(e) {
		return typeof e != "object" || !e ? null : (e = ee && e[ee] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var M = Symbol.for("react.client.reference");
	function N(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.$$typeof === M ? null : e.displayName || e.name || null;
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
			case D: return t = e.displayName || null, t === null ? N(e.type) || "Memo" : t;
			case O:
				t = e._payload, e = e._init;
				try {
					return N(e(t));
				} catch {}
		}
		return null;
	}
	var te = Array.isArray, P = n.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, F = r.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, ne = {
		pending: !1,
		data: null,
		method: null,
		action: null
	}, re = [], ie = -1;
	function ae(e) {
		return { current: e };
	}
	function oe(e) {
		0 > ie || (e.current = re[ie], re[ie] = null, ie--);
	}
	function I(e, t) {
		ie++, re[ie] = e.current, e.current = t;
	}
	var se = ae(null), ce = ae(null), le = ae(null), ue = ae(null);
	function de(e, t) {
		switch (I(le, t), I(ce, e), I(se, null), t.nodeType) {
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
		oe(se), I(se, e);
	}
	function fe() {
		oe(se), oe(ce), oe(le);
	}
	function pe(e) {
		e.memoizedState !== null && I(ue, e);
		var t = se.current, n = Hd(t, e.type);
		t !== n && (I(ce, e), I(se, n));
	}
	function me(e) {
		ce.current === e && (oe(se), oe(ce)), ue.current === e && (oe(ue), Qf._currentValue = ne);
	}
	var he, ge;
	function _e(e) {
		if (he === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			he = t && t[1] || "", ge = -1 < e.stack.indexOf("\n    at") ? " (<anonymous>)" : -1 < e.stack.indexOf("@") ? "@unknown:0:0" : "";
		}
		return "\n" + he + e + ge;
	}
	var ve = !1;
	function ye(e, t) {
		if (!e || ve) return "";
		ve = !0;
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
			ve = !1, Error.prepareStackTrace = n;
		}
		return (n = e ? e.displayName || e.name : "") ? _e(n) : "";
	}
	function be(e, t) {
		switch (e.tag) {
			case 26:
			case 27:
			case 5: return _e(e.type);
			case 16: return _e("Lazy");
			case 13: return e.child !== t && t !== null ? _e("Suspense Fallback") : _e("Suspense");
			case 19: return _e("SuspenseList");
			case 0:
			case 15: return ye(e.type, !1);
			case 11: return ye(e.type.render, !1);
			case 1: return ye(e.type, !0);
			case 31: return _e("Activity");
			default: return "";
		}
	}
	function xe(e) {
		try {
			var t = "", n = null;
			do
				t += be(e, n), n = e, e = e.return;
			while (e);
			return t;
		} catch (e) {
			return "\nError generating stack: " + e.message + "\n" + e.stack;
		}
	}
	var Se = Object.prototype.hasOwnProperty, Ce = t.unstable_scheduleCallback, we = t.unstable_cancelCallback, Te = t.unstable_shouldYield, Ee = t.unstable_requestPaint, De = t.unstable_now, Oe = t.unstable_getCurrentPriorityLevel, ke = t.unstable_ImmediatePriority, Ae = t.unstable_UserBlockingPriority, je = t.unstable_NormalPriority, Me = t.unstable_LowPriority, Ne = t.unstable_IdlePriority, Pe = t.log, Fe = t.unstable_setDisableYieldValue, Ie = null, Le = null;
	function Re(e) {
		if (typeof Pe == "function" && Fe(e), Le && typeof Le.setStrictMode == "function") try {
			Le.setStrictMode(Ie, e);
		} catch {}
	}
	var ze = Math.clz32 ? Math.clz32 : He, Be = Math.log, Ve = Math.LN2;
	function He(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (Be(e) / Ve | 0) | 0;
	}
	var Ue = 256, We = 262144, Ge = 4194304;
	function Ke(e) {
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
	function qe(e, t, n) {
		var r = e.pendingLanes;
		if (r === 0) return 0;
		var i = 0, a = e.suspendedLanes, o = e.pingedLanes;
		e = e.warmLanes;
		var s = r & 134217727;
		return s === 0 ? (s = r & ~a, s === 0 ? o === 0 ? n || (n = r & ~e, n !== 0 && (i = Ke(n))) : i = Ke(o) : i = Ke(s)) : (r = s & ~a, r === 0 ? (o &= s, o === 0 ? n || (n = s & ~e, n !== 0 && (i = Ke(n))) : i = Ke(o)) : i = Ke(r)), i === 0 ? 0 : t !== 0 && t !== i && (t & a) === 0 && (a = i & -i, n = t & -t, a >= n || a === 32 && n & 4194048) ? t : i;
	}
	function Je(e, t) {
		return (e.pendingLanes & ~(e.suspendedLanes & ~e.pingedLanes) & t) === 0;
	}
	function Ye(e, t) {
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
	function Xe() {
		var e = Ge;
		return Ge <<= 1, !(Ge & 62914560) && (Ge = 4194304), e;
	}
	function Ze(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function Qe(e, t) {
		e.pendingLanes |= t, t !== 268435456 && (e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0);
	}
	function $e(e, t, n, r, i, a) {
		var o = e.pendingLanes;
		e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0, e.expiredLanes &= n, e.entangledLanes &= n, e.errorRecoveryDisabledLanes &= n, e.shellSuspendCounter = 0;
		var s = e.entanglements, c = e.expirationTimes, l = e.hiddenUpdates;
		for (n = o & ~n; 0 < n;) {
			var u = 31 - ze(n), d = 1 << u;
			s[u] = 0, c[u] = -1;
			var f = l[u];
			if (f !== null) for (l[u] = null, u = 0; u < f.length; u++) {
				var p = f[u];
				p !== null && (p.lane &= -536870913);
			}
			n &= ~d;
		}
		r !== 0 && et(e, r, 0), a !== 0 && i === 0 && e.tag !== 0 && (e.suspendedLanes |= a & ~(o & ~t));
	}
	function et(e, t, n) {
		e.pendingLanes |= t, e.suspendedLanes &= ~t;
		var r = 31 - ze(t);
		e.entangledLanes |= t, e.entanglements[r] = e.entanglements[r] | 1073741824 | n & 261930;
	}
	function tt(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - ze(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	function nt(e, t) {
		var n = t & -t;
		return n = n & 42 ? 1 : rt(n), (n & (e.suspendedLanes | t)) === 0 ? n : 0;
	}
	function rt(e) {
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
	function it(e) {
		return e &= -e, 2 < e ? 8 < e ? e & 134217727 ? 32 : 268435456 : 8 : 2;
	}
	function at() {
		var e = F.p;
		return e === 0 ? (e = window.event, e === void 0 ? 32 : mp(e.type)) : e;
	}
	function ot(e, t) {
		var n = F.p;
		try {
			return F.p = e, t();
		} finally {
			F.p = n;
		}
	}
	var st = Math.random().toString(36).slice(2), ct = "__reactFiber$" + st, lt = "__reactProps$" + st, ut = "__reactContainer$" + st, dt = "__reactEvents$" + st, ft = "__reactListeners$" + st, pt = "__reactHandles$" + st, mt = "__reactResources$" + st, ht = "__reactMarker$" + st;
	function gt(e) {
		delete e[ct], delete e[lt], delete e[dt], delete e[ft], delete e[pt];
	}
	function _t(e) {
		var t = e[ct];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[ut] || n[ct]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = df(e); e !== null;) {
					if (n = e[ct]) return n;
					e = df(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function vt(e) {
		if (e = e[ct] || e[ut]) {
			var t = e.tag;
			if (t === 5 || t === 6 || t === 13 || t === 31 || t === 26 || t === 27 || t === 3) return e;
		}
		return null;
	}
	function yt(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e.stateNode;
		throw Error(i(33));
	}
	function bt(e) {
		var t = e[mt];
		return t || (t = e[mt] = {
			hoistableStyles: /* @__PURE__ */ new Map(),
			hoistableScripts: /* @__PURE__ */ new Map()
		}), t;
	}
	function xt(e) {
		e[ht] = !0;
	}
	var St = /* @__PURE__ */ new Set(), Ct = {};
	function wt(e, t) {
		Tt(e, t), Tt(e + "Capture", t);
	}
	function Tt(e, t) {
		for (Ct[e] = t, e = 0; e < t.length; e++) St.add(t[e]);
	}
	var Et = RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"), Dt = {}, Ot = {};
	function kt(e) {
		return Se.call(Ot, e) ? !0 : Se.call(Dt, e) ? !1 : Et.test(e) ? Ot[e] = !0 : (Dt[e] = !0, !1);
	}
	function At(e, t, n) {
		if (kt(t)) {
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
	function jt(e, t, n) {
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
	function Mt(e, t, n, r) {
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
	function Nt(e) {
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
	function Pt(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function Ft(e, t, n) {
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
	function It(e) {
		if (!e._valueTracker) {
			var t = Pt(e) ? "checked" : "value";
			e._valueTracker = Ft(e, t, "" + e[t]);
		}
	}
	function Lt(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = Pt(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== n && (t.setValue(e), !0);
	}
	function Rt(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch {
			return e.body;
		}
	}
	var zt = /[\n"\\]/g;
	function Bt(e) {
		return e.replace(zt, function(e) {
			return "\\" + e.charCodeAt(0).toString(16) + " ";
		});
	}
	function Vt(e, t, n, r, i, a, o, s) {
		e.name = "", o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" ? e.type = o : e.removeAttribute("type"), t == null ? o !== "submit" && o !== "reset" || e.removeAttribute("value") : o === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + Nt(t)) : e.value !== "" + Nt(t) && (e.value = "" + Nt(t)), t == null ? n == null ? r != null && e.removeAttribute("value") : Ut(e, o, Nt(n)) : Ut(e, o, Nt(t)), i == null && a != null && (e.defaultChecked = !!a), i != null && (e.checked = i && typeof i != "function" && typeof i != "symbol"), s != null && typeof s != "function" && typeof s != "symbol" && typeof s != "boolean" ? e.name = "" + Nt(s) : e.removeAttribute("name");
	}
	function Ht(e, t, n, r, i, a, o, s) {
		if (a != null && typeof a != "function" && typeof a != "symbol" && typeof a != "boolean" && (e.type = a), t != null || n != null) {
			if (!(a !== "submit" && a !== "reset" || t != null)) {
				It(e);
				return;
			}
			n = n == null ? "" : "" + Nt(n), t = t == null ? n : "" + Nt(t), s || t === e.value || (e.value = t), e.defaultValue = t;
		}
		r = r ?? i, r = typeof r != "function" && typeof r != "symbol" && !!r, e.checked = s ? e.checked : !!r, e.defaultChecked = !!r, o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" && (e.name = o), It(e);
	}
	function Ut(e, t, n) {
		t === "number" && Rt(e.ownerDocument) === e || e.defaultValue === "" + n || (e.defaultValue = "" + n);
	}
	function Wt(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + Nt(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function Gt(e, t, n) {
		if (t != null && (t = "" + Nt(t), t !== e.value && (e.value = t), n == null)) {
			e.defaultValue !== t && (e.defaultValue = t);
			return;
		}
		e.defaultValue = n == null ? "" : "" + Nt(n);
	}
	function Kt(e, t, n, r) {
		if (t == null) {
			if (r != null) {
				if (n != null) throw Error(i(92));
				if (te(r)) {
					if (1 < r.length) throw Error(i(93));
					r = r[0];
				}
				n = r;
			}
			n ?? (n = ""), t = n;
		}
		n = Nt(t), e.defaultValue = n, r = e.textContent, r === n && r !== "" && r !== null && (e.value = r), It(e);
	}
	function qt(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var Jt = new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));
	function Yt(e, t, n) {
		var r = t.indexOf("--") === 0;
		n == null || typeof n == "boolean" || n === "" ? r ? e.setProperty(t, "") : t === "float" ? e.cssFloat = "" : e[t] = "" : r ? e.setProperty(t, n) : typeof n != "number" || n === 0 || Jt.has(t) ? t === "float" ? e.cssFloat = n : e[t] = ("" + n).trim() : e[t] = n + "px";
	}
	function Xt(e, t, n) {
		if (t != null && typeof t != "object") throw Error(i(62));
		if (e = e.style, n != null) {
			for (var r in n) !n.hasOwnProperty(r) || t != null && t.hasOwnProperty(r) || (r.indexOf("--") === 0 ? e.setProperty(r, "") : r === "float" ? e.cssFloat = "" : e[r] = "");
			for (var a in t) r = t[a], t.hasOwnProperty(a) && n[a] !== r && Yt(e, a, r);
		} else for (var o in t) t.hasOwnProperty(o) && Yt(e, o, t[o]);
	}
	function Zt(e) {
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
	var Qt = /* @__PURE__ */ new Map([
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
	]), $t = /^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;
	function en(e) {
		return $t.test("" + e) ? "javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')" : e;
	}
	function tn() {}
	var nn = null;
	function rn(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var an = null, on = null;
	function sn(e) {
		var t = vt(e);
		if (t && (e = t.stateNode)) {
			var n = e[lt] || null;
			a: switch (e = t.stateNode, t.type) {
				case "input":
					if (Vt(e, n.value, n.defaultValue, n.defaultValue, n.checked, n.defaultChecked, n.type, n.name), t = n.name, n.type === "radio" && t != null) {
						for (n = e; n.parentNode;) n = n.parentNode;
						for (n = n.querySelectorAll("input[name=\"" + Bt("" + t) + "\"][type=\"radio\"]"), t = 0; t < n.length; t++) {
							var r = n[t];
							if (r !== e && r.form === e.form) {
								var a = r[lt] || null;
								if (!a) throw Error(i(90));
								Vt(r, a.value, a.defaultValue, a.defaultValue, a.checked, a.defaultChecked, a.type, a.name);
							}
						}
						for (t = 0; t < n.length; t++) r = n[t], r.form === e.form && Lt(r);
					}
					break a;
				case "textarea":
					Gt(e, n.value, n.defaultValue);
					break a;
				case "select": t = n.value, t != null && Wt(e, !!n.multiple, t, !1);
			}
		}
	}
	var cn = !1;
	function ln(e, t, n) {
		if (cn) return e(t, n);
		cn = !0;
		try {
			return e(t);
		} finally {
			if (cn = !1, (an !== null || on !== null) && (vu(), an && (t = an, e = on, on = an = null, sn(t), e))) for (t = 0; t < e.length; t++) sn(e[t]);
		}
	}
	function un(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var r = n[lt] || null;
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
	var dn = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), fn = !1;
	if (dn) try {
		var pn = {};
		Object.defineProperty(pn, "passive", { get: function() {
			fn = !0;
		} }), window.addEventListener("test", pn, pn), window.removeEventListener("test", pn, pn);
	} catch {
		fn = !1;
	}
	var mn = null, hn = null, gn = null;
	function _n() {
		if (gn) return gn;
		var e, t = hn, n = t.length, r, i = "value" in mn ? mn.value : mn.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return gn = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function vn(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function yn() {
		return !0;
	}
	function bn() {
		return !1;
	}
	function xn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? yn : bn, this.isPropagationStopped = bn, this;
		}
		return h(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = yn);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = yn);
			},
			persist: function() {},
			isPersistent: yn
		}), t;
	}
	var Sn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Cn = xn(Sn), wn = h({}, Sn, {
		view: 0,
		detail: 0
	}), Tn = xn(wn), En, Dn, On, kn = h({}, wn, {
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
		getModifierState: zn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== On && (On && e.type === "mousemove" ? (En = e.screenX - On.screenX, Dn = e.screenY - On.screenY) : Dn = En = 0, On = e), En);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : Dn;
		}
	}), An = xn(kn), jn = xn(h({}, kn, { dataTransfer: 0 })), Mn = xn(h({}, wn, { relatedTarget: 0 })), L = xn(h({}, Sn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Nn = xn(h({}, Sn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Pn = xn(h({}, Sn, { data: 0 })), Fn = {
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
	}, In = {
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
	}, Ln = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Rn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Ln[e]) ? !!t[e] : !1;
	}
	function zn() {
		return Rn;
	}
	var Bn = xn(h({}, wn, {
		key: function(e) {
			if (e.key) {
				var t = Fn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = vn(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? In[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: zn,
		charCode: function(e) {
			return e.type === "keypress" ? vn(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? vn(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), Vn = xn(h({}, kn, {
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
	})), Hn = xn(h({}, wn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: zn
	})), Un = xn(h({}, Sn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Wn = xn(h({}, kn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), R = xn(h({}, Sn, {
		newState: 0,
		oldState: 0
	})), Gn = [
		9,
		13,
		27,
		32
	], Kn = dn && "CompositionEvent" in window, qn = null;
	dn && "documentMode" in document && (qn = document.documentMode);
	var Jn = dn && "TextEvent" in window && !qn, Yn = dn && (!Kn || qn && 8 < qn && 11 >= qn), Xn = " ", Zn = !1;
	function Qn(e, t) {
		switch (e) {
			case "keyup": return Gn.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function $n(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var er = !1;
	function tr(e, t) {
		switch (e) {
			case "compositionend": return $n(t);
			case "keypress": return t.which === 32 ? (Zn = !0, Xn) : null;
			case "textInput": return e = t.data, e === Xn && Zn ? null : e;
			default: return null;
		}
	}
	function nr(e, t) {
		if (er) return e === "compositionend" || !Kn && Qn(e, t) ? (e = _n(), gn = hn = mn = null, er = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return Yn && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var rr = {
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
	function ir(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!rr[e.type] : t === "textarea";
	}
	function ar(e, t, n, r) {
		an ? on ? on.push(r) : on = [r] : an = r, t = Td(t, "onChange"), 0 < t.length && (n = new Cn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var or = null, sr = null;
	function cr(e) {
		vd(e, 0);
	}
	function z(e) {
		if (Lt(yt(e))) return e;
	}
	function lr(e, t) {
		if (e === "change") return t;
	}
	var ur = !1;
	if (dn) {
		var dr;
		if (dn) {
			var fr = "oninput" in document;
			if (!fr) {
				var pr = document.createElement("div");
				pr.setAttribute("oninput", "return;"), fr = typeof pr.oninput == "function";
			}
			dr = fr;
		} else dr = !1;
		ur = dr && (!document.documentMode || 9 < document.documentMode);
	}
	function mr() {
		or && (or.detachEvent("onpropertychange", hr), sr = or = null);
	}
	function hr(e) {
		if (e.propertyName === "value" && z(sr)) {
			var t = [];
			ar(t, sr, e, rn(e)), ln(cr, t);
		}
	}
	function gr(e, t, n) {
		e === "focusin" ? (mr(), or = t, sr = n, or.attachEvent("onpropertychange", hr)) : e === "focusout" && mr();
	}
	function _r(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return z(sr);
	}
	function vr(e, t) {
		if (e === "click") return z(t);
	}
	function yr(e, t) {
		if (e === "input" || e === "change") return z(t);
	}
	function br(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var xr = typeof Object.is == "function" ? Object.is : br;
	function Sr(e, t) {
		if (xr(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!Se.call(t, i) || !xr(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Cr(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function wr(e, t) {
		var n = Cr(e);
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
			n = Cr(n);
		}
	}
	function Tr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Tr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function Er(e) {
		e = e != null && e.ownerDocument != null && e.ownerDocument.defaultView != null ? e.ownerDocument.defaultView : window;
		for (var t = Rt(e.document); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = Rt(e.document);
		}
		return t;
	}
	function Dr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	var Or = dn && "documentMode" in document && 11 >= document.documentMode, kr = null, Ar = null, jr = null, Mr = !1;
	function Nr(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Mr || kr == null || kr !== Rt(r) || (r = kr, "selectionStart" in r && Dr(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), jr && Sr(jr, r) || (jr = r, r = Td(Ar, "onSelect"), 0 < r.length && (t = new Cn("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = kr)));
	}
	function Pr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Fr = {
		animationend: Pr("Animation", "AnimationEnd"),
		animationiteration: Pr("Animation", "AnimationIteration"),
		animationstart: Pr("Animation", "AnimationStart"),
		transitionrun: Pr("Transition", "TransitionRun"),
		transitionstart: Pr("Transition", "TransitionStart"),
		transitioncancel: Pr("Transition", "TransitionCancel"),
		transitionend: Pr("Transition", "TransitionEnd")
	}, Ir = {}, Lr = {};
	dn && (Lr = document.createElement("div").style, "AnimationEvent" in window || (delete Fr.animationend.animation, delete Fr.animationiteration.animation, delete Fr.animationstart.animation), "TransitionEvent" in window || delete Fr.transitionend.transition);
	function Rr(e) {
		if (Ir[e]) return Ir[e];
		if (!Fr[e]) return e;
		var t = Fr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in Lr) return Ir[e] = t[n];
		return e;
	}
	var zr = Rr("animationend"), Br = Rr("animationiteration"), Vr = Rr("animationstart"), Hr = Rr("transitionrun"), Ur = Rr("transitionstart"), Wr = Rr("transitioncancel"), Gr = Rr("transitionend"), Kr = /* @__PURE__ */ new Map(), qr = "abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	qr.push("scrollEnd");
	function Jr(e, t) {
		Kr.set(e, t), wt(t, [e]);
	}
	var Yr = typeof reportError == "function" ? reportError : function(e) {
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
	}, Xr = [], Zr = 0, Qr = 0;
	function $r() {
		for (var e = Zr, t = Qr = Zr = 0; t < e;) {
			var n = Xr[t];
			Xr[t++] = null;
			var r = Xr[t];
			Xr[t++] = null;
			var i = Xr[t];
			Xr[t++] = null;
			var a = Xr[t];
			if (Xr[t++] = null, r !== null && i !== null) {
				var o = r.pending;
				o === null ? i.next = i : (i.next = o.next, o.next = i), r.pending = i;
			}
			a !== 0 && ri(n, i, a);
		}
	}
	function ei(e, t, n, r) {
		Xr[Zr++] = e, Xr[Zr++] = t, Xr[Zr++] = n, Xr[Zr++] = r, Qr |= r, e.lanes |= r, e = e.alternate, e !== null && (e.lanes |= r);
	}
	function ti(e, t, n, r) {
		return ei(e, t, n, r), ii(e);
	}
	function ni(e, t) {
		return ei(e, null, null, t), ii(e);
	}
	function ri(e, t, n) {
		e.lanes |= n;
		var r = e.alternate;
		r !== null && (r.lanes |= n);
		for (var i = !1, a = e.return; a !== null;) a.childLanes |= n, r = a.alternate, r !== null && (r.childLanes |= n), a.tag === 22 && (e = a.stateNode, e === null || e._visibility & 1 || (i = !0)), e = a, a = a.return;
		return e.tag === 3 ? (a = e.stateNode, i && t !== null && (i = 31 - ze(n), e = a.hiddenUpdates, r = e[i], r === null ? e[i] = [t] : r.push(t), t.lane = n | 536870912), a) : null;
	}
	function ii(e) {
		if (50 < lu) throw lu = 0, uu = null, Error(i(185));
		for (var t = e.return; t !== null;) e = t, t = e.return;
		return e.tag === 3 ? e.stateNode : null;
	}
	var ai = {};
	function oi(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.refCleanup = this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function si(e, t, n, r) {
		return new oi(e, t, n, r);
	}
	function ci(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function li(e, t) {
		var n = e.alternate;
		return n === null ? (n = si(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 65011712, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n.refCleanup = e.refCleanup, n;
	}
	function ui(e, t) {
		e.flags &= 65011714;
		var n = e.alternate;
		return n === null ? (e.childLanes = 0, e.lanes = t, e.child = null, e.subtreeFlags = 0, e.memoizedProps = null, e.memoizedState = null, e.updateQueue = null, e.dependencies = null, e.stateNode = null) : (e.childLanes = n.childLanes, e.lanes = n.lanes, e.child = n.child, e.subtreeFlags = 0, e.deletions = null, e.memoizedProps = n.memoizedProps, e.memoizedState = n.memoizedState, e.updateQueue = n.updateQueue, e.type = n.type, t = n.dependencies, e.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}), e;
	}
	function di(e, t, n, r, a, o) {
		var s = 0;
		if (r = e, typeof e == "function") ci(e) && (s = 1);
		else if (typeof e == "string") s = Uf(e, n, se.current) ? 26 : e === "html" || e === "head" || e === "body" ? 27 : 5;
		else a: switch (e) {
			case k: return e = si(31, n, t, a), e.elementType = k, e.lanes = o, e;
			case y: return fi(n.children, a, o, t);
			case b:
				s = 8, a |= 24;
				break;
			case x: return e = si(12, n, t, a | 2), e.elementType = x, e.lanes = o, e;
			case T: return e = si(13, n, t, a), e.elementType = T, e.lanes = o, e;
			case E: return e = si(19, n, t, a), e.elementType = E, e.lanes = o, e;
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
		return t = si(s, n, t, a), t.elementType = e, t.type = r, t.lanes = o, t;
	}
	function fi(e, t, n, r) {
		return e = si(7, e, r, t), e.lanes = n, e;
	}
	function pi(e, t, n) {
		return e = si(6, e, null, t), e.lanes = n, e;
	}
	function mi(e) {
		var t = si(18, null, null, 0);
		return t.stateNode = e, t;
	}
	function hi(e, t, n) {
		return t = si(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	var gi = /* @__PURE__ */ new WeakMap();
	function _i(e, t) {
		if (typeof e == "object" && e) {
			var n = gi.get(e);
			return n === void 0 ? (t = {
				value: e,
				source: t,
				stack: xe(t)
			}, gi.set(e, t), t) : n;
		}
		return {
			value: e,
			source: t,
			stack: xe(t)
		};
	}
	var vi = [], yi = 0, bi = null, xi = 0, Si = [], Ci = 0, wi = null, Ti = 1, Ei = "";
	function Di(e, t) {
		vi[yi++] = xi, vi[yi++] = bi, bi = e, xi = t;
	}
	function Oi(e, t, n) {
		Si[Ci++] = Ti, Si[Ci++] = Ei, Si[Ci++] = wi, wi = e;
		var r = Ti;
		e = Ei;
		var i = 32 - ze(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - ze(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, Ti = 1 << 32 - ze(t) + i | n << i | r, Ei = a + e;
		} else Ti = 1 << a | n << i | r, Ei = e;
	}
	function ki(e) {
		e.return !== null && (Di(e, 1), Oi(e, 1, 0));
	}
	function Ai(e) {
		for (; e === bi;) bi = vi[--yi], vi[yi] = null, xi = vi[--yi], vi[yi] = null;
		for (; e === wi;) wi = Si[--Ci], Si[Ci] = null, Ei = Si[--Ci], Si[Ci] = null, Ti = Si[--Ci], Si[Ci] = null;
	}
	function ji(e, t) {
		Si[Ci++] = Ti, Si[Ci++] = Ei, Si[Ci++] = wi, Ti = t.id, Ei = t.overflow, wi = e;
	}
	var Mi = null, Ni = null, B = !1, Pi = null, Fi = !1, Ii = Error(i(519));
	function Li(e) {
		throw Ui(_i(Error(i(418, 1 < arguments.length && arguments[1] !== void 0 && arguments[1] ? "text" : "HTML", "")), e)), Ii;
	}
	function Ri(e) {
		var t = e.stateNode, n = e.type, r = e.memoizedProps;
		switch (t[ct] = e, t[lt] = r, n) {
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
				$("invalid", t), Ht(t, r.value, r.defaultValue, r.checked, r.defaultChecked, r.type, r.name, !0);
				break;
			case "select":
				$("invalid", t);
				break;
			case "textarea": $("invalid", t), Kt(t, r.value, r.defaultValue, r.children);
		}
		n = r.children, typeof n != "string" && typeof n != "number" && typeof n != "bigint" || t.textContent === "" + n || !0 === r.suppressHydrationWarning || jd(t.textContent, n) ? (r.popover != null && ($("beforetoggle", t), $("toggle", t)), r.onScroll != null && $("scroll", t), r.onScrollEnd != null && $("scrollend", t), r.onClick != null && (t.onclick = tn), t = !0) : t = !1, t || Li(e, !0);
	}
	function zi(e) {
		for (Mi = e.return; Mi;) switch (Mi.tag) {
			case 5:
			case 31:
			case 13:
				Fi = !1;
				return;
			case 27:
			case 3:
				Fi = !0;
				return;
			default: Mi = Mi.return;
		}
	}
	function Bi(e) {
		if (e !== Mi) return !1;
		if (!B) return zi(e), B = !0, !1;
		var t = e.tag, n;
		if ((n = t !== 3 && t !== 27) && ((n = t === 5) && (n = e.type, n = n === "form" || n === "button" || Ud(e.type, e.memoizedProps)), n = !n), n && Ni && Li(e), zi(e), t === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			Ni = uf(e);
		} else if (t === 31) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			Ni = uf(e);
		} else t === 27 ? (t = Ni, Zd(e.type) ? (e = lf, lf = null, Ni = e) : Ni = t) : Ni = Mi ? cf(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Vi() {
		Ni = Mi = null, B = !1;
	}
	function Hi() {
		var e = Pi;
		return e !== null && (Yl === null ? Yl = e : Yl.push.apply(Yl, e), Pi = null), e;
	}
	function Ui(e) {
		Pi === null ? Pi = [e] : Pi.push(e);
	}
	var Wi = ae(null), Gi = null, Ki = null;
	function qi(e, t, n) {
		I(Wi, t._currentValue), t._currentValue = n;
	}
	function Ji(e) {
		e._currentValue = Wi.current, oe(Wi);
	}
	function Yi(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function Xi(e, t, n, r) {
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
						o.lanes |= n, c = o.alternate, c !== null && (c.lanes |= n), Yi(o.return, n, e), r || (s = null);
						break a;
					}
					o = c.next;
				}
			} else if (a.tag === 18) {
				if (s = a.return, s === null) throw Error(i(341));
				s.lanes |= n, o = s.alternate, o !== null && (o.lanes |= n), Yi(s, n, e), s = null;
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
	function Zi(e, t, n, r) {
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
					xr(a.pendingProps.value, s.value) || (e === null ? e = [c] : e.push(c));
				}
			} else if (a === ue.current) {
				if (s = a.alternate, s === null) throw Error(i(387));
				s.memoizedState.memoizedState !== a.memoizedState.memoizedState && (e === null ? e = [Qf] : e.push(Qf));
			}
			a = a.return;
		}
		e !== null && Xi(t, e, n, r), t.flags |= 262144;
	}
	function Qi(e) {
		for (e = e.firstContext; e !== null;) {
			if (!xr(e.context._currentValue, e.memoizedValue)) return !0;
			e = e.next;
		}
		return !1;
	}
	function $i(e) {
		Gi = e, Ki = null, e = e.dependencies, e !== null && (e.firstContext = null);
	}
	function ea(e) {
		return na(Gi, e);
	}
	function ta(e, t) {
		return Gi === null && $i(e), na(e, t);
	}
	function na(e, t) {
		var n = t._currentValue;
		if (t = {
			context: t,
			memoizedValue: n,
			next: null
		}, Ki === null) {
			if (e === null) throw Error(i(308));
			Ki = t, e.dependencies = {
				lanes: 0,
				firstContext: t
			}, e.flags |= 524288;
		} else Ki = Ki.next = t;
		return n;
	}
	var ra = typeof AbortController < "u" ? AbortController : function() {
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
	}, ia = t.unstable_scheduleCallback, aa = t.unstable_NormalPriority, oa = {
		$$typeof: C,
		Consumer: null,
		Provider: null,
		_currentValue: null,
		_currentValue2: null,
		_threadCount: 0
	};
	function sa() {
		return {
			controller: new ra(),
			data: /* @__PURE__ */ new Map(),
			refCount: 0
		};
	}
	function ca(e) {
		e.refCount--, e.refCount === 0 && ia(aa, function() {
			e.controller.abort();
		});
	}
	var la = null, ua = 0, da = 0, fa = null;
	function pa(e, t) {
		if (la === null) {
			var n = la = [];
			ua = 0, da = ud(), fa = {
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
	var ga = P.S;
	P.S = function(e, t) {
		Ql = De(), typeof t == "object" && t && typeof t.then == "function" && pa(e, t), ga !== null && ga(e, t);
	};
	var _a = ae(null);
	function va() {
		var e = _a.current;
		return e === null ? Fl.pooledCache : e;
	}
	function ya(e, t) {
		t === null ? I(_a, _a.current) : I(_a, t.pool);
	}
	function ba() {
		var e = va();
		return e === null ? null : {
			parent: oa._currentValue,
			pool: e
		};
	}
	var xa = Error(i(460)), Sa = Error(i(474)), Ca = Error(i(542)), wa = { then: function() {} };
	function Ta(e) {
		return e = e.status, e === "fulfilled" || e === "rejected";
	}
	function Ea(e, t, n) {
		switch (n = e[n], n === void 0 ? e.push(t) : n !== t && (t.then(tn, tn), t = n), t.status) {
			case "fulfilled": return t.value;
			case "rejected": throw e = t.reason, Aa(e), e;
			default:
				if (typeof t.status == "string") t.then(tn, tn);
				else {
					if (e = Fl, e !== null && 100 < e.shellSuspendCounter) throw Error(i(482));
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
					case "rejected": throw e = t.reason, Aa(e), e;
				}
				throw Oa = t, xa;
		}
	}
	function Da(e) {
		try {
			var t = e._init;
			return t(e._payload);
		} catch (e) {
			throw typeof e == "object" && e && typeof e.then == "function" ? (Oa = e, xa) : e;
		}
	}
	var Oa = null;
	function ka() {
		if (Oa === null) throw Error(i(459));
		var e = Oa;
		return Oa = null, e;
	}
	function Aa(e) {
		if (e === xa || e === Ca) throw Error(i(483));
	}
	var ja = null, Ma = 0;
	function Na(e) {
		var t = Ma;
		return Ma += 1, ja === null && (ja = []), Ea(ja, e, t);
	}
	function Pa(e, t) {
		t = t.props.ref, e.ref = t === void 0 ? null : t;
	}
	function Fa(e, t) {
		throw t.$$typeof === g ? Error(i(525)) : (e = Object.prototype.toString.call(t), Error(i(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e)));
	}
	function Ia(e) {
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
			return e = li(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 67108866, n) : (r = r.index, r < n ? (t.flags |= 67108866, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 67108866), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = pi(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === y ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === O && Da(i) === t.type) ? (t = a(t, n.props), Pa(t, n), t.return = e, t) : (t = di(n.type, n.key, n.props, null, e.mode, r), Pa(t, n), t.return = e, t);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = hi(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = fi(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number" || typeof t == "bigint") return t = pi("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case _: return n = di(t.type, t.key, t.props, null, e.mode, n), Pa(n, t), n.return = e, n;
					case v: return t = hi(t, e.mode, n), t.return = e, t;
					case O: return t = Da(t), f(e, t, n);
				}
				if (te(t) || j(t)) return t = fi(t, e.mode, n, null), t.return = e, t;
				if (typeof t.then == "function") return f(e, Na(t), n);
				if (t.$$typeof === C) return f(e, ta(e, t), n);
				Fa(e, t);
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
					case O: return n = Da(n), p(e, t, n, r);
				}
				if (te(n) || j(n)) return i === null ? d(e, t, n, r, null) : null;
				if (typeof n.then == "function") return p(e, t, Na(n), r);
				if (n.$$typeof === C) return p(e, t, ta(e, n), r);
				Fa(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number" || typeof r == "bigint") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case _: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case v: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case O: return r = Da(r), m(e, t, n, r, i);
				}
				if (te(r) || j(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				if (typeof r.then == "function") return m(e, t, n, Na(r), i);
				if (r.$$typeof === C) return m(e, t, n, ta(t, r), i);
				Fa(t, r);
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
			if (h === s.length) return n(i, d), B && Di(i, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(i, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return B && Di(i, h), l;
			}
			for (d = r(d); h < s.length; h++) g = m(d, i, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(i, e);
			}), B && Di(i, h), l;
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
			if (v.done) return n(a, h), B && Di(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return B && Di(a, g), u;
			}
			for (h = r(h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), B && Di(a, g), u;
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
									} else if (r.elementType === l || typeof l == "object" && l && l.$$typeof === O && Da(l) === r.type) {
										n(e, r.sibling), c = a(r, o.props), Pa(c, o), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							o.type === y ? (c = fi(o.props.children, e.mode, c, o.key), c.return = e, e = c) : (c = di(o.type, o.key, o.props, null, e.mode, c), Pa(c, o), c.return = e, e = c);
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
							c = hi(o, e.mode, c), c.return = e, e = c;
						}
						return s(e);
					case O: return o = Da(o), b(e, r, o, c);
				}
				if (te(o)) return h(e, r, o, c);
				if (j(o)) {
					if (l = j(o), typeof l != "function") throw Error(i(150));
					return o = l.call(o), g(e, r, o, c);
				}
				if (typeof o.then == "function") return b(e, r, Na(o), c);
				if (o.$$typeof === C) return b(e, r, ta(e, o), c);
				Fa(e, o);
			}
			return typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint" ? (o = "" + o, r !== null && r.tag === 6 ? (n(e, r.sibling), c = a(r, o), c.return = e, e = c) : (n(e, r), c = pi(o, e.mode, c), c.return = e, e = c), s(e)) : n(e, r);
		}
		return function(e, t, n, r) {
			try {
				Ma = 0;
				var i = b(e, t, n, r);
				return ja = null, i;
			} catch (t) {
				if (t === xa || t === Ca) throw t;
				var a = si(29, t, null, e.mode);
				return a.lanes = r, a.return = e, a;
			}
		};
	}
	var La = Ia(!0), Ra = Ia(!1), za = !1;
	function Ba(e) {
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
	function Va(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			callbacks: null
		});
	}
	function Ha(e) {
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
		if (r = r.shared, Pl & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, t = ii(e), ri(e, null, n), t;
		}
		return ei(e, r, t, n), ii(e);
	}
	function Wa(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194048)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, tt(e, n);
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
	function qa() {
		if (Ka) {
			var e = fa;
			if (e !== null) throw e;
		}
	}
	function Ja(e, t, n, r) {
		Ka = !1;
		var i = e.updateQueue;
		za = !1;
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
				if (p ? (Q & f) === f : (r & f) === f) {
					f !== 0 && f === da && (Ka = !0), u !== null && (u = u.next = {
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
							case 2: za = !0;
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
			u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, a === null && (i.shared.lanes = 0), Ul |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function Ya(e, t) {
		if (typeof e != "function") throw Error(i(191, e));
		e.call(t);
	}
	function Xa(e, t) {
		var n = e.callbacks;
		if (n !== null) for (e.callbacks = null, e = 0; e < n.length; e++) Ya(n[e], t);
	}
	var Za = ae(null), Qa = ae(0);
	function $a(e, t) {
		e = Vl, I(Qa, e), I(Za, t), Vl = e | t.baseLanes;
	}
	function eo() {
		I(Qa, Vl), I(Za, Za.current);
	}
	function to() {
		Vl = Qa.current, oe(Za), oe(Qa);
	}
	var no = ae(null), ro = null;
	function io(e) {
		var t = e.alternate;
		I(V, V.current & 1), I(no, e), ro === null && (t === null || Za.current !== null || t.memoizedState !== null) && (ro = e);
	}
	function ao(e) {
		I(V, V.current), I(no, e), ro === null && (ro = e);
	}
	function oo(e) {
		e.tag === 22 ? (I(V, V.current), I(no, e), ro === null && (ro = e)) : so(e);
	}
	function so() {
		I(V, V.current), I(no, no.current);
	}
	function co(e) {
		oe(no), ro === e && (ro = null), oe(V);
	}
	var V = ae(0);
	function lo(e) {
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
	var uo = 0, H = null, fo = null, po = null, U = !1, mo = !1, W = !1, ho = 0, G = 0, go = null, _o = 0;
	function vo() {
		throw Error(i(321));
	}
	function yo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!xr(e[n], t[n])) return !1;
		return !0;
	}
	function bo(e, t, n, r, i, a) {
		return uo = a, H = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, P.H = e === null || e.memoizedState === null ? Ms : Ns, W = !1, a = n(r, i), W = !1, mo && (a = xo(t, n, r, i)), K(e), a;
	}
	function K(e) {
		P.H = js;
		var t = fo !== null && fo.next !== null;
		if (uo = 0, po = fo = H = null, U = !1, G = 0, go = null, t) throw Error(i(300));
		e === null || Xs || (e = e.dependencies, e !== null && Qi(e) && (Xs = !0));
	}
	function xo(e, t, n, r) {
		H = e;
		var a = 0;
		do {
			if (mo && (go = null), G = 0, mo = !1, 25 <= a) throw Error(i(301));
			if (a += 1, po = fo = null, e.updateQueue != null) {
				var o = e.updateQueue;
				o.lastEffect = null, o.events = null, o.stores = null, o.memoCache != null && (o.memoCache.index = 0);
			}
			P.H = Ps, o = t(n, r);
		} while (mo);
		return o;
	}
	function So() {
		var e = P.H, t = e.useState()[0];
		return t = typeof t.then == "function" ? To(t) : t, e = e.useState()[0], (fo === null ? null : fo.memoizedState) !== e && (H.flags |= 1024), t;
	}
	function q() {
		var e = ho !== 0;
		return ho = 0, e;
	}
	function Co(e, t, n) {
		t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~n;
	}
	function J(e) {
		if (U) {
			for (e = e.memoizedState; e !== null;) {
				var t = e.queue;
				t !== null && (t.pending = null), e = e.next;
			}
			U = !1;
		}
		uo = 0, po = fo = H = null, mo = !1, G = ho = 0, go = null;
	}
	function Y() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return po === null ? H.memoizedState = po = e : po = po.next = e, po;
	}
	function X() {
		if (fo === null) {
			var e = H.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = fo.next;
		var t = po === null ? H.memoizedState : po.next;
		if (t !== null) po = t, fo = e;
		else {
			if (e === null) throw H.alternate === null ? Error(i(467)) : Error(i(310));
			fo = e, e = {
				memoizedState: fo.memoizedState,
				baseState: fo.baseState,
				baseQueue: fo.baseQueue,
				queue: fo.queue,
				next: null
			}, po === null ? H.memoizedState = po = e : po = po.next = e;
		}
		return po;
	}
	function wo() {
		return {
			lastEffect: null,
			events: null,
			stores: null,
			memoCache: null
		};
	}
	function To(e) {
		var t = G;
		return G += 1, go === null && (go = []), e = Ea(go, e, t), t = H, (po === null ? t.memoizedState : po.next) === null && (t = t.alternate, P.H = t === null || t.memoizedState === null ? Ms : Ns), e;
	}
	function Eo(e) {
		if (typeof e == "object" && e) {
			if (typeof e.then == "function") return To(e);
			if (e.$$typeof === C) return ea(e);
		}
		throw Error(i(438, String(e)));
	}
	function Do(e) {
		var t = null, n = H.updateQueue;
		if (n !== null && (t = n.memoCache), t == null) {
			var r = H.alternate;
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
		}), n === null && (n = wo(), H.updateQueue = n), n.memoCache = t, n = t.data[t.index], n === void 0) for (n = t.data[t.index] = Array(e), r = 0; r < e; r++) n[r] = A;
		return t.index++, n;
	}
	function Oo(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function ko(e) {
		return Ao(X(), fo, e);
	}
	function Ao(e, t, n) {
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
				if (f === u.lane ? (uo & f) === f : (Q & f) === f) {
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
					else if ((uo & p) === p) {
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
					}, l === null ? (c = l = f, s = o) : l = l.next = f, H.lanes |= p, Ul |= p;
					f = u.action, W && n(o, f), o = u.hasEagerState ? u.eagerState : n(o, f);
				} else p = {
					lane: f,
					revertLane: u.revertLane,
					gesture: u.gesture,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}, l === null ? (c = l = p, s = o) : l = l.next = p, H.lanes |= f, Ul |= f;
				u = u.next;
			} while (u !== null && u !== t);
			if (l === null ? s = o : l.next = c, !xr(o, e.memoizedState) && (Xs = !0, d && (n = fa, n !== null))) throw n;
			e.memoizedState = o, e.baseState = s, e.baseQueue = l, r.lastRenderedState = o;
		}
		return a === null && (r.lanes = 0), [e.memoizedState, r.dispatch];
	}
	function jo(e) {
		var t = X(), n = t.queue;
		if (n === null) throw Error(i(311));
		n.lastRenderedReducer = e;
		var r = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			xr(o, t.memoizedState) || (Xs = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, r];
	}
	function Mo(e, t, n) {
		var r = H, a = X(), o = B;
		if (o) {
			if (n === void 0) throw Error(i(407));
			n = n();
		} else n = t();
		var s = !xr((fo || a).memoizedState, n);
		if (s && (a.memoizedState = n, Xs = !0), a = a.queue, rs(Fo.bind(null, r, a, e), [e]), a.getSnapshot !== t || s || po !== null && po.memoizedState.tag & 1) {
			if (r.flags |= 2048, Qo(9, { destroy: void 0 }, Po.bind(null, r, a, n, t), null), Fl === null) throw Error(i(349));
			o || uo & 127 || No(r, t, n);
		}
		return n;
	}
	function No(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = H.updateQueue, t === null ? (t = wo(), H.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function Po(e, t, n, r) {
		t.value = n, t.getSnapshot = r, Io(t) && Lo(e);
	}
	function Fo(e, t, n) {
		return n(function() {
			Io(t) && Lo(e);
		});
	}
	function Io(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !xr(e, n);
		} catch {
			return !0;
		}
	}
	function Lo(e) {
		var t = ni(e, 2);
		t !== null && pu(t, e, 2);
	}
	function Ro(e) {
		var t = Y();
		if (typeof e == "function") {
			var n = e;
			if (e = n(), W) {
				Re(!0);
				try {
					n();
				} finally {
					Re(!1);
				}
			}
		}
		return t.memoizedState = t.baseState = e, t.queue = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Oo,
			lastRenderedState: e
		}, t;
	}
	function zo(e, t, n, r) {
		return e.baseState = n, Ao(e, fo, typeof r == "function" ? r : Oo);
	}
	function Bo(e, t, n, r, a) {
		if (Os(e)) throw Error(i(485));
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
			P.T === null ? o.isTransition = !1 : n(!0), r(o), n = t.pending, n === null ? (o.next = t.pending = o, Vo(t, o)) : (o.next = n.next, t.pending = n.next = o);
		}
	}
	function Vo(e, t) {
		var n = t.action, r = t.payload, i = e.state;
		if (t.isTransition) {
			var a = P.T, o = {};
			P.T = o;
			try {
				var s = n(i, r), c = P.S;
				c !== null && c(o, s), Ho(e, t, s);
			} catch (n) {
				Wo(e, t, n);
			} finally {
				a !== null && o.types !== null && (a.types = o.types), P.T = a;
			}
		} else try {
			a = n(i, r), Ho(e, t, a);
		} catch (n) {
			Wo(e, t, n);
		}
	}
	function Ho(e, t, n) {
		typeof n == "object" && n && typeof n.then == "function" ? n.then(function(n) {
			Uo(e, t, n);
		}, function(n) {
			return Wo(e, t, n);
		}) : Uo(e, t, n);
	}
	function Uo(e, t, n) {
		t.status = "fulfilled", t.value = n, Go(t), e.state = n, t = e.pending, t !== null && (n = t.next, n === t ? e.pending = null : (n = n.next, t.next = n, Vo(e, n)));
	}
	function Wo(e, t, n) {
		var r = e.pending;
		if (e.pending = null, r !== null) {
			r = r.next;
			do
				t.status = "rejected", t.reason = n, Go(t), t = t.next;
			while (t !== r);
		}
		e.action = null;
	}
	function Go(e) {
		e = e.listeners;
		for (var t = 0; t < e.length; t++) (0, e[t])();
	}
	function Ko(e, t) {
		return t;
	}
	function qo(e, t) {
		if (B) {
			var n = Fl.formState;
			if (n !== null) {
				a: {
					var r = H;
					if (B) {
						if (Ni) {
							b: {
								for (var i = Ni, a = Fi; i.nodeType !== 8;) {
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
								Ni = cf(i.nextSibling), r = i.data === "F!";
								break a;
							}
						}
						Li(r);
					}
					r = !1;
				}
				r && (t = n[0]);
			}
		}
		return n = Y(), n.memoizedState = n.baseState = t, r = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Ko,
			lastRenderedState: t
		}, n.queue = r, n = Ts.bind(null, H, r), r.dispatch = n, r = Ro(!1), a = Ds.bind(null, H, !1, r.queue), r = Y(), i = {
			state: t,
			dispatch: null,
			action: e,
			pending: null
		}, r.queue = i, n = Bo.bind(null, H, i, a, n), i.dispatch = n, r.memoizedState = e, [
			t,
			n,
			!1
		];
	}
	function Jo(e) {
		return Yo(X(), fo, e);
	}
	function Yo(e, t, n) {
		if (t = Ao(e, t, Ko)[0], e = ko(Oo)[0], typeof t == "object" && t && typeof t.then == "function") try {
			var r = To(t);
		} catch (e) {
			throw e === xa ? Ca : e;
		}
		else r = t;
		t = X();
		var i = t.queue, a = i.dispatch;
		return n !== t.memoizedState && (H.flags |= 2048, Qo(9, { destroy: void 0 }, Xo.bind(null, i, n), null)), [
			r,
			a,
			e
		];
	}
	function Xo(e, t) {
		e.action = t;
	}
	function Zo(e) {
		var t = X(), n = fo;
		if (n !== null) return Yo(t, n, e);
		X(), t = t.memoizedState, n = X();
		var r = n.queue.dispatch;
		return n.memoizedState = e, [
			t,
			r,
			!1
		];
	}
	function Qo(e, t, n, r) {
		return e = {
			tag: e,
			create: n,
			deps: r,
			inst: t,
			next: null
		}, t = H.updateQueue, t === null && (t = wo(), H.updateQueue = t), n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e), e;
	}
	function $o() {
		return X().memoizedState;
	}
	function es(e, t, n, r) {
		var i = Y();
		H.flags |= e, i.memoizedState = Qo(1 | t, { destroy: void 0 }, n, r === void 0 ? null : r);
	}
	function ts(e, t, n, r) {
		var i = X();
		r = r === void 0 ? null : r;
		var a = i.memoizedState.inst;
		fo !== null && r !== null && yo(r, fo.memoizedState.deps) ? i.memoizedState = Qo(t, a, n, r) : (H.flags |= e, i.memoizedState = Qo(1 | t, a, n, r));
	}
	function ns(e, t) {
		es(8390656, 8, e, t);
	}
	function rs(e, t) {
		ts(2048, 8, e, t);
	}
	function is(e) {
		H.flags |= 4;
		var t = H.updateQueue;
		if (t === null) t = wo(), H.updateQueue = t, t.events = [e];
		else {
			var n = t.events;
			n === null ? t.events = [e] : n.push(e);
		}
	}
	function as(e) {
		var t = X().memoizedState;
		return is({
			ref: t,
			nextImpl: e
		}), function() {
			if (Pl & 2) throw Error(i(440));
			return t.impl.apply(void 0, arguments);
		};
	}
	function os(e, t) {
		return ts(4, 2, e, t);
	}
	function ss(e, t) {
		return ts(4, 4, e, t);
	}
	function cs(e, t) {
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
	function ls(e, t, n) {
		n = n == null ? null : n.concat([e]), ts(4, 4, cs.bind(null, t, e), n);
	}
	function us() {}
	function ds(e, t) {
		var n = X();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return t !== null && yo(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function fs(e, t) {
		var n = X();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		if (t !== null && yo(t, r[1])) return r[0];
		if (r = e(), W) {
			Re(!0);
			try {
				e();
			} finally {
				Re(!1);
			}
		}
		return n.memoizedState = [r, t], r;
	}
	function ps(e, t, n) {
		return n === void 0 || uo & 1073741824 && !(Q & 261930) ? e.memoizedState = t : (e.memoizedState = n, e = fu(), H.lanes |= e, Ul |= e, n);
	}
	function ms(e, t, n, r) {
		return xr(n, t) ? n : Za.current === null ? !(uo & 42) || uo & 1073741824 && !(Q & 261930) ? (Xs = !0, e.memoizedState = n) : (e = fu(), H.lanes |= e, Ul |= e, t) : (e = ps(e, n, r), xr(e, t) || (Xs = !0), e);
	}
	function hs(e, t, n, r, i) {
		var a = F.p;
		F.p = a !== 0 && 8 > a ? a : 8;
		var o = P.T, s = {};
		P.T = s, Ds(e, !1, t, n);
		try {
			var c = i(), l = P.S;
			l !== null && l(s, c), typeof c == "object" && c && typeof c.then == "function" ? Es(e, t, ha(c, r), du(e)) : Es(e, t, r, du(e));
		} catch (n) {
			Es(e, t, {
				then: function() {},
				status: "rejected",
				reason: n
			}, du());
		} finally {
			F.p = a, o !== null && s.types !== null && (o.types = s.types), P.T = o;
		}
	}
	function gs() {}
	function _s(e, t, n, r) {
		if (e.tag !== 5) throw Error(i(476));
		var a = vs(e).queue;
		hs(e, a, t, ne, n === null ? gs : function() {
			return ys(e), n(r);
		});
	}
	function vs(e) {
		var t = e.memoizedState;
		if (t !== null) return t;
		t = {
			memoizedState: ne,
			baseState: ne,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: Oo,
				lastRenderedState: ne
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
				lastRenderedReducer: Oo,
				lastRenderedState: n
			},
			next: null
		}, e.memoizedState = t, e = e.alternate, e !== null && (e.memoizedState = t), t;
	}
	function ys(e) {
		var t = vs(e);
		t.next === null && (t = e.alternate.memoizedState), Es(e, t.next.queue, {}, du());
	}
	function bs() {
		return ea(Qf);
	}
	function xs() {
		return X().memoizedState;
	}
	function Ss() {
		return X().memoizedState;
	}
	function Cs(e) {
		for (var t = e.return; t !== null;) {
			switch (t.tag) {
				case 24:
				case 3:
					var n = du();
					e = Ha(n);
					var r = Ua(t, e, n);
					r !== null && (pu(r, t, n), Wa(r, t, n)), t = { cache: sa() }, e.payload = t;
					return;
			}
			t = t.return;
		}
	}
	function ws(e, t, n) {
		var r = du();
		n = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, Os(e) ? ks(t, n) : (n = ti(e, t, n, r), n !== null && (pu(n, e, r), As(n, t, r)));
	}
	function Ts(e, t, n) {
		Es(e, t, n, du());
	}
	function Es(e, t, n, r) {
		var i = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (Os(e)) ks(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, xr(s, o)) return ei(e, t, i, 0), Fl === null && $r(), !1;
			} catch {}
			if (n = ti(e, t, i, r), n !== null) return pu(n, e, r), As(n, t, r), !0;
		}
		return !1;
	}
	function Ds(e, t, n, r) {
		if (r = {
			lane: 2,
			revertLane: ud(),
			gesture: null,
			action: r,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, Os(e)) {
			if (t) throw Error(i(479));
		} else t = ti(e, n, r, 2), t !== null && pu(t, e, 2);
	}
	function Os(e) {
		var t = e.alternate;
		return e === H || t !== null && t === H;
	}
	function ks(e, t) {
		mo = U = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function As(e, t, n) {
		if (n & 4194048) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, tt(e, n);
		}
	}
	var js = {
		readContext: ea,
		use: Eo,
		useCallback: vo,
		useContext: vo,
		useEffect: vo,
		useImperativeHandle: vo,
		useLayoutEffect: vo,
		useInsertionEffect: vo,
		useMemo: vo,
		useReducer: vo,
		useRef: vo,
		useState: vo,
		useDebugValue: vo,
		useDeferredValue: vo,
		useTransition: vo,
		useSyncExternalStore: vo,
		useId: vo,
		useHostTransitionStatus: vo,
		useFormState: vo,
		useActionState: vo,
		useOptimistic: vo,
		useMemoCache: vo,
		useCacheRefresh: vo
	};
	js.useEffectEvent = vo;
	var Ms = {
		readContext: ea,
		use: Eo,
		useCallback: function(e, t) {
			return Y().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: ea,
		useEffect: ns,
		useImperativeHandle: function(e, t, n) {
			n = n == null ? null : n.concat([e]), es(4194308, 4, cs.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return es(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			es(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = Y();
			t = t === void 0 ? null : t;
			var r = e();
			if (W) {
				Re(!0);
				try {
					e();
				} finally {
					Re(!1);
				}
			}
			return n.memoizedState = [r, t], r;
		},
		useReducer: function(e, t, n) {
			var r = Y();
			if (n !== void 0) {
				var i = n(t);
				if (W) {
					Re(!0);
					try {
						n(t);
					} finally {
						Re(!1);
					}
				}
			} else i = t;
			return r.memoizedState = r.baseState = i, e = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: i
			}, r.queue = e, e = e.dispatch = ws.bind(null, H, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = Y();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: function(e) {
			e = Ro(e);
			var t = e.queue, n = Ts.bind(null, H, t);
			return t.dispatch = n, [e.memoizedState, n];
		},
		useDebugValue: us,
		useDeferredValue: function(e, t) {
			return ps(Y(), e, t);
		},
		useTransition: function() {
			var e = Ro(!1);
			return e = hs.bind(null, H, e.queue, !0, !1), Y().memoizedState = e, [!1, e];
		},
		useSyncExternalStore: function(e, t, n) {
			var r = H, a = Y();
			if (B) {
				if (n === void 0) throw Error(i(407));
				n = n();
			} else {
				if (n = t(), Fl === null) throw Error(i(349));
				Q & 127 || No(r, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, ns(Fo.bind(null, r, o, e), [e]), r.flags |= 2048, Qo(9, { destroy: void 0 }, Po.bind(null, r, o, n, t), null), n;
		},
		useId: function() {
			var e = Y(), t = Fl.identifierPrefix;
			if (B) {
				var n = Ei, r = Ti;
				n = (r & ~(1 << 32 - ze(r) - 1)).toString(32) + n, t = "_" + t + "R_" + n, n = ho++, 0 < n && (t += "H" + n.toString(32)), t += "_";
			} else n = _o++, t = "_" + t + "r_" + n.toString(32) + "_";
			return e.memoizedState = t;
		},
		useHostTransitionStatus: bs,
		useFormState: qo,
		useActionState: qo,
		useOptimistic: function(e) {
			var t = Y();
			t.memoizedState = t.baseState = e;
			var n = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: null,
				lastRenderedState: null
			};
			return t.queue = n, t = Ds.bind(null, H, !0, n), n.dispatch = t, [e, t];
		},
		useMemoCache: Do,
		useCacheRefresh: function() {
			return Y().memoizedState = Cs.bind(null, H);
		},
		useEffectEvent: function(e) {
			var t = Y(), n = { impl: e };
			return t.memoizedState = n, function() {
				if (Pl & 2) throw Error(i(440));
				return n.impl.apply(void 0, arguments);
			};
		}
	}, Ns = {
		readContext: ea,
		use: Eo,
		useCallback: ds,
		useContext: ea,
		useEffect: rs,
		useImperativeHandle: ls,
		useInsertionEffect: os,
		useLayoutEffect: ss,
		useMemo: fs,
		useReducer: ko,
		useRef: $o,
		useState: function() {
			return ko(Oo);
		},
		useDebugValue: us,
		useDeferredValue: function(e, t) {
			return ms(X(), fo.memoizedState, e, t);
		},
		useTransition: function() {
			var e = ko(Oo)[0], t = X().memoizedState;
			return [typeof e == "boolean" ? e : To(e), t];
		},
		useSyncExternalStore: Mo,
		useId: xs,
		useHostTransitionStatus: bs,
		useFormState: Jo,
		useActionState: Jo,
		useOptimistic: function(e, t) {
			return zo(X(), fo, e, t);
		},
		useMemoCache: Do,
		useCacheRefresh: Ss
	};
	Ns.useEffectEvent = as;
	var Ps = {
		readContext: ea,
		use: Eo,
		useCallback: ds,
		useContext: ea,
		useEffect: rs,
		useImperativeHandle: ls,
		useInsertionEffect: os,
		useLayoutEffect: ss,
		useMemo: fs,
		useReducer: jo,
		useRef: $o,
		useState: function() {
			return jo(Oo);
		},
		useDebugValue: us,
		useDeferredValue: function(e, t) {
			var n = X();
			return fo === null ? ps(n, e, t) : ms(n, fo.memoizedState, e, t);
		},
		useTransition: function() {
			var e = jo(Oo)[0], t = X().memoizedState;
			return [typeof e == "boolean" ? e : To(e), t];
		},
		useSyncExternalStore: Mo,
		useId: xs,
		useHostTransitionStatus: bs,
		useFormState: Zo,
		useActionState: Zo,
		useOptimistic: function(e, t) {
			var n = X();
			return fo === null ? (n.baseState = e, [e, n.queue.dispatch]) : zo(n, fo, e, t);
		},
		useMemoCache: Do,
		useCacheRefresh: Ss
	};
	Ps.useEffectEvent = as;
	function Fs(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : h({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var Is = {
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = du(), i = Ha(r);
			i.payload = t, n != null && (i.callback = n), t = Ua(e, i, r), t !== null && (pu(t, e, r), Wa(t, e, r));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = du(), i = Ha(r);
			i.tag = 1, i.payload = t, n != null && (i.callback = n), t = Ua(e, i, r), t !== null && (pu(t, e, r), Wa(t, e, r));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = du(), r = Ha(n);
			r.tag = 2, t != null && (r.callback = t), t = Ua(e, r, n), t !== null && (pu(t, e, n), Wa(t, e, n));
		}
	};
	function Ls(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Sr(n, r) || !Sr(i, a) : !0;
	}
	function Rs(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && Is.enqueueReplaceState(t, t.state, null);
	}
	function zs(e, t) {
		var n = t;
		if ("ref" in t) for (var r in n = {}, t) r !== "ref" && (n[r] = t[r]);
		if (e = e.defaultProps) for (var i in n === t && (n = h({}, n)), e) n[i] === void 0 && (n[i] = e[i]);
		return n;
	}
	function Bs(e) {
		Yr(e);
	}
	function Vs(e) {
		console.error(e);
	}
	function Hs(e) {
		Yr(e);
	}
	function Us(e, t) {
		try {
			var n = e.onUncaughtError;
			n(t.value, { componentStack: t.stack });
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function Ws(e, t, n) {
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
	function Gs(e, t, n) {
		return n = Ha(n), n.tag = 3, n.payload = { element: null }, n.callback = function() {
			Us(e, t);
		}, n;
	}
	function Ks(e) {
		return e = Ha(e), e.tag = 3, e;
	}
	function qs(e, t, n, r) {
		var i = n.type.getDerivedStateFromError;
		if (typeof i == "function") {
			var a = r.value;
			e.payload = function() {
				return i(a);
			}, e.callback = function() {
				Ws(t, n, r);
			};
		}
		var o = n.stateNode;
		o !== null && typeof o.componentDidCatch == "function" && (e.callback = function() {
			Ws(t, n, r), typeof i != "function" && (tu === null ? tu = /* @__PURE__ */ new Set([this]) : tu.add(this));
			var e = r.stack;
			this.componentDidCatch(r.value, { componentStack: e === null ? "" : e });
		});
	}
	function Js(e, t, n, r, a) {
		if (n.flags |= 32768, typeof r == "object" && r && typeof r.then == "function") {
			if (t = n.alternate, t !== null && Zi(t, n, a, !0), n = no.current, n !== null) {
				switch (n.tag) {
					case 31:
					case 13: return ro === null ? Tu() : n.alternate === null && Hl === 0 && (Hl = 3), n.flags &= -257, n.flags |= 65536, n.lanes = a, r === wa ? n.flags |= 16384 : (t = n.updateQueue, t === null ? n.updateQueue = /* @__PURE__ */ new Set([r]) : t.add(r), Wu(e, r, a)), !1;
					case 22: return n.flags |= 65536, r === wa ? n.flags |= 16384 : (t = n.updateQueue, t === null ? (t = {
						transitions: null,
						markerInstances: null,
						retryQueue: /* @__PURE__ */ new Set([r])
					}, n.updateQueue = t) : (n = t.retryQueue, n === null ? t.retryQueue = /* @__PURE__ */ new Set([r]) : n.add(r)), Wu(e, r, a)), !1;
				}
				throw Error(i(435, n.tag));
			}
			return Wu(e, r, a), Tu(), !1;
		}
		if (B) return t = no.current, t === null ? (r !== Ii && (t = Error(i(423), { cause: r }), Ui(_i(t, n))), e = e.current.alternate, e.flags |= 65536, a &= -a, e.lanes |= a, r = _i(r, n), a = Gs(e.stateNode, r, a), Ga(e, a), Hl !== 4 && (Hl = 2)) : (!(t.flags & 65536) && (t.flags |= 256), t.flags |= 65536, t.lanes = a, r !== Ii && (e = Error(i(422), { cause: r }), Ui(_i(e, n)))), !1;
		var o = Error(i(520), { cause: r });
		if (o = _i(o, n), Jl === null ? Jl = [o] : Jl.push(o), Hl !== 4 && (Hl = 2), t === null) return !0;
		r = _i(r, n), n = t;
		do {
			switch (n.tag) {
				case 3: return n.flags |= 65536, e = a & -a, n.lanes |= e, e = Gs(n.stateNode, r, e), Ga(n, e), !1;
				case 1: if (t = n.type, o = n.stateNode, !(n.flags & 128) && (typeof t.getDerivedStateFromError == "function" || o !== null && typeof o.componentDidCatch == "function" && (tu === null || !tu.has(o)))) return n.flags |= 65536, a &= -a, n.lanes |= a, a = Ks(a), qs(a, e, n, r), Ga(n, a), !1;
			}
			n = n.return;
		} while (n !== null);
		return !1;
	}
	var Ys = Error(i(461)), Xs = !1;
	function Zs(e, t, n, r) {
		t.child = e === null ? Ra(t, null, n, r) : La(t, e.child, n, r);
	}
	function Qs(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		if ("ref" in r) {
			var o = {};
			for (var s in r) s !== "ref" && (o[s] = r[s]);
		} else o = r;
		return $i(t), r = bo(e, t, n, o, a, i), s = q(), e !== null && !Xs ? (Co(e, t, i), Sc(e, t, i)) : (B && s && ki(t), t.flags |= 1, Zs(e, t, r, i), t.child);
	}
	function $s(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !ci(a) && a.defaultProps === void 0 && n.compare === null ? (t.tag = 15, t.type = a, ec(e, t, a, r, i)) : (e = di(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, !Cc(e, i)) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Sr : n, n(o, r) && e.ref === t.ref) return Sc(e, t, i);
		}
		return t.flags |= 1, e = li(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function ec(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Sr(a, r) && e.ref === t.ref) {
				if (Xs = !1, t.pendingProps = r = a, Cc(e, i)) e.flags & 131072 && (Xs = !0);
				else return t.lanes = e.lanes, Sc(e, t, i);
			}
		}
		return cc(e, t, n, r, i);
	}
	function tc(e, t, n, r) {
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
				return rc(e, t, a, n, r);
			}
			if (n & 536870912) t.memoizedState = {
				baseLanes: 0,
				cachePool: null
			}, e !== null && ya(t, a === null ? null : a.cachePool), a === null ? eo() : $a(t, a), oo(t);
			else return r = t.lanes = 536870912, rc(e, t, a === null ? n : a.baseLanes | n, n, r);
		} else a === null ? (e !== null && ya(t, null), eo(), so(t)) : (ya(t, a.cachePool), $a(t, a), so(t), t.memoizedState = null);
		return Zs(e, t, i, n), t.child;
	}
	function nc(e, t) {
		return e !== null && e.tag === 22 || t.stateNode !== null || (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), t.sibling;
	}
	function rc(e, t, n, r, i) {
		var a = va();
		return a = a === null ? null : {
			parent: oa._currentValue,
			pool: a
		}, t.memoizedState = {
			baseLanes: n,
			cachePool: a
		}, e !== null && ya(t, null), eo(), oo(t), e !== null && Zi(e, t, r, !0), t.childLanes = i, null;
	}
	function ic(e, t) {
		return t = _c({
			mode: t.mode,
			children: t.children
		}, e.mode), t.ref = e.ref, e.child = t, t.return = e, t;
	}
	function ac(e, t, n) {
		return La(t, e.child, null, n), e = ic(t, t.pendingProps), e.flags |= 2, co(t), t.memoizedState = null, e;
	}
	function oc(e, t, n) {
		var r = t.pendingProps, a = !!(t.flags & 128);
		if (t.flags &= -129, e === null) {
			if (B) {
				if (r.mode === "hidden") return e = ic(t, r), t.lanes = 536870912, nc(null, e);
				if (ao(t), (e = Ni) ? (e = rf(e, Fi), e = e !== null && e.data === "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: wi === null ? null : {
						id: Ti,
						overflow: Ei
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = mi(e), n.return = t, t.child = n, Mi = t, Ni = null)) : e = null, e === null) throw Li(t);
				return t.lanes = 536870912, null;
			}
			return ic(t, r);
		}
		var o = e.memoizedState;
		if (o !== null) {
			var s = o.dehydrated;
			if (ao(t), a) {
				if (t.flags & 256) t.flags &= -257, t = ac(e, t, n);
				else if (t.memoizedState !== null) t.child = e.child, t.flags |= 128, t = null;
				else throw Error(i(558));
			} else if (Xs || Zi(e, t, n, !1), a = (n & e.childLanes) !== 0, Xs || a) {
				if (r = Fl, r !== null && (s = nt(r, n), s !== 0 && s !== o.retryLane)) throw o.retryLane = s, ni(e, s), pu(r, e, s), Ys;
				Tu(), t = ac(e, t, n);
			} else e = o.treeContext, Ni = cf(s.nextSibling), Mi = t, B = !0, Pi = null, Fi = !1, e !== null && ji(t, e), t = ic(t, r), t.flags |= 4096;
			return t;
		}
		return e = li(e.child, {
			mode: r.mode,
			children: r.children
		}), e.ref = t.ref, t.child = e, e.return = t, e;
	}
	function sc(e, t) {
		var n = t.ref;
		if (n === null) e !== null && e.ref !== null && (t.flags |= 4194816);
		else {
			if (typeof n != "function" && typeof n != "object") throw Error(i(284));
			(e === null || e.ref !== n) && (t.flags |= 4194816);
		}
	}
	function cc(e, t, n, r, i) {
		return $i(t), n = bo(e, t, n, r, void 0, i), r = q(), e !== null && !Xs ? (Co(e, t, i), Sc(e, t, i)) : (B && r && ki(t), t.flags |= 1, Zs(e, t, n, i), t.child);
	}
	function lc(e, t, n, r, i, a) {
		return $i(t), t.updateQueue = null, n = xo(t, r, n, i), K(e), r = q(), e !== null && !Xs ? (Co(e, t, a), Sc(e, t, a)) : (B && r && ki(t), t.flags |= 1, Zs(e, t, n, a), t.child);
	}
	function uc(e, t, n, r, i) {
		if ($i(t), t.stateNode === null) {
			var a = ai, o = n.contextType;
			typeof o == "object" && o && (a = ea(o)), a = new n(r, a), t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, a.updater = Is, t.stateNode = a, a._reactInternals = t, a = t.stateNode, a.props = r, a.state = t.memoizedState, a.refs = {}, Ba(t), o = n.contextType, a.context = typeof o == "object" && o ? ea(o) : ai, a.state = t.memoizedState, o = n.getDerivedStateFromProps, typeof o == "function" && (Fs(t, n, o, r), a.state = t.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof a.getSnapshotBeforeUpdate == "function" || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (o = a.state, typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount(), o !== a.state && Is.enqueueReplaceState(a, a.state, null), Ja(t, r, a, i), qa(), a.state = t.memoizedState), typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !0;
		} else if (e === null) {
			a = t.stateNode;
			var s = t.memoizedProps, c = zs(n, s);
			a.props = c;
			var l = a.context, u = n.contextType;
			o = ai, typeof u == "object" && u && (o = ea(u));
			var d = n.getDerivedStateFromProps;
			u = typeof d == "function" || typeof a.getSnapshotBeforeUpdate == "function", s = t.pendingProps !== s, u || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (s || l !== o) && Rs(t, a, r, o), za = !1;
			var f = t.memoizedState;
			a.state = f, Ja(t, r, a, i), qa(), l = t.memoizedState, s || f !== l || za ? (typeof d == "function" && (Fs(t, n, d, r), l = t.memoizedState), (c = za || Ls(t, n, c, r, f, l, o)) ? (u || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = l), a.props = r, a.state = l, a.context = o, r = c) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			a = t.stateNode, Va(e, t), o = t.memoizedProps, u = zs(n, o), a.props = u, d = t.pendingProps, f = a.context, l = n.contextType, c = ai, typeof l == "object" && l && (c = ea(l)), s = n.getDerivedStateFromProps, (l = typeof s == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (o !== d || f !== c) && Rs(t, a, r, c), za = !1, f = t.memoizedState, a.state = f, Ja(t, r, a, i), qa();
			var p = t.memoizedState;
			o !== d || f !== p || za || e !== null && e.dependencies !== null && Qi(e.dependencies) ? (typeof s == "function" && (Fs(t, n, s, r), p = t.memoizedState), (u = za || Ls(t, n, u, r, f, p, c) || e !== null && e.dependencies !== null && Qi(e.dependencies)) ? (l || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(r, p, c), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(r, p, c)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = p), a.props = r, a.state = p, a.context = c, r = u) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return a = r, sc(e, t), r = !!(t.flags & 128), a || r ? (a = t.stateNode, n = r && typeof n.getDerivedStateFromError != "function" ? null : a.render(), t.flags |= 1, e !== null && r ? (t.child = La(t, e.child, null, i), t.child = La(t, null, n, i)) : Zs(e, t, n, i), t.memoizedState = a.state, e = t.child) : e = Sc(e, t, i), e;
	}
	function dc(e, t, n, r) {
		return Vi(), t.flags |= 256, Zs(e, t, n, r), t.child;
	}
	var fc = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0,
		hydrationErrors: null
	};
	function pc(e) {
		return {
			baseLanes: e,
			cachePool: ba()
		};
	}
	function mc(e, t, n) {
		return e = e === null ? 0 : e.childLanes & ~n, t && (e |= Kl), e;
	}
	function hc(e, t, n) {
		var r = t.pendingProps, a = !1, o = !!(t.flags & 128), s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : !!(V.current & 2)), s && (a = !0, t.flags &= -129), s = !!(t.flags & 32), t.flags &= -33, e === null) {
			if (B) {
				if (a ? io(t) : so(t), (e = Ni) ? (e = rf(e, Fi), e = e !== null && e.data !== "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: wi === null ? null : {
						id: Ti,
						overflow: Ei
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = mi(e), n.return = t, t.child = n, Mi = t, Ni = null)) : e = null, e === null) throw Li(t);
				return of(e) ? t.lanes = 32 : t.lanes = 536870912, null;
			}
			var c = r.children;
			return r = r.fallback, a ? (so(t), a = t.mode, c = _c({
				mode: "hidden",
				children: c
			}, a), r = fi(r, a, n, null), c.return = t, r.return = t, c.sibling = r, t.child = c, r = t.child, r.memoizedState = pc(n), r.childLanes = mc(e, s, n), t.memoizedState = fc, nc(null, r)) : (io(t), gc(t, c));
		}
		var l = e.memoizedState;
		if (l !== null && (c = l.dehydrated, c !== null)) {
			if (o) t.flags & 256 ? (io(t), t.flags &= -257, t = vc(e, t, n)) : t.memoizedState === null ? (so(t), c = r.fallback, a = t.mode, r = _c({
				mode: "visible",
				children: r.children
			}, a), c = fi(c, a, n, null), c.flags |= 2, r.return = t, c.return = t, r.sibling = c, t.child = r, La(t, e.child, null, n), r = t.child, r.memoizedState = pc(n), r.childLanes = mc(e, s, n), t.memoizedState = fc, t = nc(null, r)) : (so(t), t.child = e.child, t.flags |= 128, t = null);
			else if (io(t), of(c)) {
				if (s = c.nextSibling && c.nextSibling.dataset, s) var u = s.dgst;
				s = u, r = Error(i(419)), r.stack = "", r.digest = s, Ui({
					value: r,
					source: null,
					stack: null
				}), t = vc(e, t, n);
			} else if (Xs || Zi(e, t, n, !1), s = (n & e.childLanes) !== 0, Xs || s) {
				if (s = Fl, s !== null && (r = nt(s, n), r !== 0 && r !== l.retryLane)) throw l.retryLane = r, ni(e, r), pu(s, e, r), Ys;
				af(c) || Tu(), t = vc(e, t, n);
			} else af(c) ? (t.flags |= 192, t.child = e.child, t = null) : (e = l.treeContext, Ni = cf(c.nextSibling), Mi = t, B = !0, Pi = null, Fi = !1, e !== null && ji(t, e), t = gc(t, r.children), t.flags |= 4096);
			return t;
		}
		return a ? (so(t), c = r.fallback, a = t.mode, l = e.child, u = l.sibling, r = li(l, {
			mode: "hidden",
			children: r.children
		}), r.subtreeFlags = l.subtreeFlags & 65011712, u === null ? (c = fi(c, a, n, null), c.flags |= 2) : c = li(u, c), c.return = t, r.return = t, r.sibling = c, t.child = r, nc(null, r), r = t.child, c = e.child.memoizedState, c === null ? c = pc(n) : (a = c.cachePool, a === null ? a = ba() : (l = oa._currentValue, a = a.parent === l ? a : {
			parent: l,
			pool: l
		}), c = {
			baseLanes: c.baseLanes | n,
			cachePool: a
		}), r.memoizedState = c, r.childLanes = mc(e, s, n), t.memoizedState = fc, nc(e.child, r)) : (io(t), n = e.child, e = n.sibling, n = li(n, {
			mode: "visible",
			children: r.children
		}), n.return = t, n.sibling = null, e !== null && (s = t.deletions, s === null ? (t.deletions = [e], t.flags |= 16) : s.push(e)), t.child = n, t.memoizedState = null, n);
	}
	function gc(e, t) {
		return t = _c({
			mode: "visible",
			children: t
		}, e.mode), t.return = e, e.child = t;
	}
	function _c(e, t) {
		return e = si(22, e, null, t), e.lanes = 0, e;
	}
	function vc(e, t, n) {
		return La(t, e.child, null, n), e = gc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function yc(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), Yi(e.return, t, n);
	}
	function bc(e, t, n, r, i, a) {
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
	function xc(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		r = r.children;
		var o = V.current, s = !!(o & 2);
		if (s ? (o = o & 1 | 2, t.flags |= 128) : o &= 1, I(V, o), Zs(e, t, r, n), r = B ? xi : 0, !s && e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
			if (e.tag === 13) e.memoizedState !== null && yc(e, n, t);
			else if (e.tag === 19) yc(e, n, t);
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
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && lo(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), bc(t, !1, i, n, a, r);
				break;
			case "backwards":
			case "unstable_legacy-backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && lo(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				bc(t, !0, n, null, a, r);
				break;
			case "together":
				bc(t, !1, null, null, void 0, r);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function Sc(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), Ul |= t.lanes, (n & t.childLanes) === 0) {
			if (e !== null) {
				if (Zi(e, t, n, !1), (n & t.childLanes) === 0) return null;
			} else return null;
		}
		if (e !== null && t.child !== e.child) throw Error(i(153));
		if (t.child !== null) {
			for (e = t.child, n = li(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = li(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function Cc(e, t) {
		return (e.lanes & t) !== 0 || (e = e.dependencies, !!(e !== null && Qi(e)));
	}
	function wc(e, t, n) {
		switch (t.tag) {
			case 3:
				de(t, t.stateNode.containerInfo), qi(t, oa, e.memoizedState.cache), Vi();
				break;
			case 27:
			case 5:
				pe(t);
				break;
			case 4:
				de(t, t.stateNode.containerInfo);
				break;
			case 10:
				qi(t, t.type, t.memoizedProps.value);
				break;
			case 31:
				if (t.memoizedState !== null) return t.flags |= 128, ao(t), null;
				break;
			case 13:
				var r = t.memoizedState;
				if (r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (io(t), e = Sc(e, t, n), e === null ? null : e.sibling) : hc(e, t, n) : (io(t), t.flags |= 128, null);
				io(t);
				break;
			case 19:
				var i = !!(e.flags & 128);
				if (r = (n & t.childLanes) !== 0, r || (Zi(e, t, n, !1), r = (n & t.childLanes) !== 0), i) {
					if (r) return xc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), I(V, V.current), r) break;
				return null;
			case 22: return t.lanes = 0, tc(e, t, n, t.pendingProps);
			case 24: qi(t, oa, e.memoizedState.cache);
		}
		return Sc(e, t, n);
	}
	function Tc(e, t, n) {
		if (e !== null) {
			if (e.memoizedProps !== t.pendingProps) Xs = !0;
			else {
				if (!Cc(e, n) && !(t.flags & 128)) return Xs = !1, wc(e, t, n);
				Xs = !!(e.flags & 131072);
			}
		} else Xs = !1, B && t.flags & 1048576 && Oi(t, xi, t.index);
		switch (t.lanes = 0, t.tag) {
			case 16:
				a: {
					var r = t.pendingProps;
					if (e = Da(t.elementType), t.type = e, typeof e == "function") ci(e) ? (r = zs(e, r), t.tag = 1, t = uc(null, t, e, r, n)) : (t.tag = 0, t = cc(null, t, e, r, n));
					else {
						if (e != null) {
							var a = e.$$typeof;
							if (a === w) {
								t.tag = 11, t = Qs(null, t, e, r, n);
								break a;
							}
							if (a === D) {
								t.tag = 14, t = $s(null, t, e, r, n);
								break a;
							}
						}
						throw t = N(e) || e, Error(i(306, t, ""));
					}
				}
				return t;
			case 0: return cc(e, t, t.type, t.pendingProps, n);
			case 1: return r = t.type, a = zs(r, t.pendingProps), uc(e, t, r, a, n);
			case 3:
				a: {
					if (de(t, t.stateNode.containerInfo), e === null) throw Error(i(387));
					r = t.pendingProps;
					var o = t.memoizedState;
					a = o.element, Va(e, t), Ja(t, r, null, n);
					var s = t.memoizedState;
					if (r = s.cache, qi(t, oa, r), r !== o.cache && Xi(t, [oa], n, !0), qa(), r = s.element, o.isDehydrated) {
						if (o = {
							element: r,
							isDehydrated: !1,
							cache: s.cache
						}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
							t = dc(e, t, r, n);
							break a;
						}
						if (r !== a) {
							a = _i(Error(i(424)), t), Ui(a), t = dc(e, t, r, n);
							break a;
						}
						switch (e = t.stateNode.containerInfo, e.nodeType) {
							case 9:
								e = e.body;
								break;
							default: e = e.nodeName === "HTML" ? e.ownerDocument.body : e;
						}
						for (Ni = cf(e.firstChild), Mi = t, B = !0, Pi = null, Fi = !0, n = Ra(t, null, r, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					} else {
						if (Vi(), r === a) {
							t = Sc(e, t, n);
							break a;
						}
						Zs(e, t, r, n);
					}
					t = t.child;
				}
				return t;
			case 26: return sc(e, t), e === null ? (n = kf(t.type, null, t.pendingProps, null)) ? t.memoizedState = n : B || (n = t.type, e = t.pendingProps, r = Bd(le.current).createElement(n), r[ct] = t, r[lt] = e, Pd(r, n, e), xt(r), t.stateNode = r) : t.memoizedState = kf(t.type, e.memoizedProps, t.pendingProps, e.memoizedState), null;
			case 27: return pe(t), e === null && B && (r = t.stateNode = ff(t.type, t.pendingProps, le.current), Mi = t, Fi = !0, a = Ni, Zd(t.type) ? (lf = a, Ni = cf(r.firstChild)) : Ni = a), Zs(e, t, t.pendingProps.children, n), sc(e, t), e === null && (t.flags |= 4194304), t.child;
			case 5: return e === null && B && ((a = r = Ni) && (r = tf(r, t.type, t.pendingProps, Fi), r === null ? a = !1 : (t.stateNode = r, Mi = t, Ni = cf(r.firstChild), Fi = !1, a = !0)), a || Li(t)), pe(t), a = t.type, o = t.pendingProps, s = e === null ? null : e.memoizedProps, r = o.children, Ud(a, o) ? r = null : s !== null && Ud(a, s) && (t.flags |= 32), t.memoizedState !== null && (a = bo(e, t, So, null, null, n), Qf._currentValue = a), sc(e, t), Zs(e, t, r, n), t.child;
			case 6: return e === null && B && ((e = n = Ni) && (n = nf(n, t.pendingProps, Fi), n === null ? e = !1 : (t.stateNode = n, Mi = t, Ni = null, e = !0)), e || Li(t)), null;
			case 13: return hc(e, t, n);
			case 4: return de(t, t.stateNode.containerInfo), r = t.pendingProps, e === null ? t.child = La(t, null, r, n) : Zs(e, t, r, n), t.child;
			case 11: return Qs(e, t, t.type, t.pendingProps, n);
			case 7: return Zs(e, t, t.pendingProps, n), t.child;
			case 8: return Zs(e, t, t.pendingProps.children, n), t.child;
			case 12: return Zs(e, t, t.pendingProps.children, n), t.child;
			case 10: return r = t.pendingProps, qi(t, t.type, r.value), Zs(e, t, r.children, n), t.child;
			case 9: return a = t.type._context, r = t.pendingProps.children, $i(t), a = ea(a), r = r(a), t.flags |= 1, Zs(e, t, r, n), t.child;
			case 14: return $s(e, t, t.type, t.pendingProps, n);
			case 15: return ec(e, t, t.type, t.pendingProps, n);
			case 19: return xc(e, t, n);
			case 31: return oc(e, t, n);
			case 22: return tc(e, t, n, t.pendingProps);
			case 24: return $i(t), r = ea(oa), e === null ? (a = va(), a === null && (a = Fl, o = sa(), a.pooledCache = o, o.refCount++, o !== null && (a.pooledCacheLanes |= n), a = o), t.memoizedState = {
				parent: r,
				cache: a
			}, Ba(t), qi(t, oa, a)) : ((e.lanes & n) !== 0 && (Va(e, t), Ja(t, null, null, n), qa()), a = e.memoizedState, o = t.memoizedState, a.parent === r ? (r = o.cache, qi(t, oa, r), r !== a.cache && Xi(t, [oa], n, !0)) : (a = {
				parent: r,
				cache: r
			}, t.memoizedState = a, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = a), qi(t, oa, r))), Zs(e, t, t.pendingProps.children, n), t.child;
			case 29: throw t.pendingProps;
		}
		throw Error(i(156, t.tag));
	}
	function Ec(e) {
		e.flags |= 4;
	}
	function Dc(e, t, n, r, i) {
		if ((t = !!(e.mode & 32)) && (t = !1), t) {
			if (e.flags |= 16777216, (i & 335544128) === i) {
				if (e.stateNode.complete) e.flags |= 8192;
				else if (Su()) e.flags |= 8192;
				else throw Oa = wa, Sa;
			}
		} else e.flags &= -16777217;
	}
	function Oc(e, t) {
		if (t.type !== "stylesheet" || t.state.loading & 4) e.flags &= -16777217;
		else if (e.flags |= 16777216, !Wf(t)) {
			if (Su()) e.flags |= 8192;
			else throw Oa = wa, Sa;
		}
	}
	function kc(e, t) {
		t !== null && (e.flags |= 4), e.flags & 16384 && (t = e.tag === 22 ? 536870912 : Xe(), e.lanes |= t, ql |= t);
	}
	function Ac(e, t) {
		if (!B) switch (e.tailMode) {
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
	function jc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 65011712, r |= i.flags & 65011712, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function Mc(e, t, n) {
		var r = t.pendingProps;
		switch (Ai(t), t.tag) {
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return jc(t), null;
			case 1: return jc(t), null;
			case 3: return n = t.stateNode, r = null, e !== null && (r = e.memoizedState.cache), t.memoizedState.cache !== r && (t.flags |= 2048), Ji(oa), fe(), n.pendingContext && (n.context = n.pendingContext, n.pendingContext = null), (e === null || e.child === null) && (Bi(t) ? Ec(t) : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Hi())), jc(t), null;
			case 26:
				var a = t.type, o = t.memoizedState;
				return e === null ? (Ec(t), o === null ? (jc(t), Dc(t, a, null, r, n)) : (jc(t), Oc(t, o))) : o ? o === e.memoizedState ? (jc(t), t.flags &= -16777217) : (Ec(t), jc(t), Oc(t, o)) : (e = e.memoizedProps, e !== r && Ec(t), jc(t), Dc(t, a, e, r, n)), null;
			case 27:
				if (me(t), n = le.current, a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && Ec(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return jc(t), null;
					}
					e = se.current, Bi(t) ? Ri(t, e) : (e = ff(a, r, n), t.stateNode = e, Ec(t));
				}
				return jc(t), null;
			case 5:
				if (me(t), a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && Ec(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return jc(t), null;
					}
					if (o = se.current, Bi(t)) Ri(t, o);
					else {
						var s = Bd(le.current);
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
						o[ct] = t, o[lt] = r;
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
						r && Ec(t);
					}
				}
				return jc(t), Dc(t, t.type, e === null ? null : e.memoizedProps, t.pendingProps, n), null;
			case 6:
				if (e && t.stateNode != null) e.memoizedProps !== r && Ec(t);
				else {
					if (typeof r != "string" && t.stateNode === null) throw Error(i(166));
					if (e = le.current, Bi(t)) {
						if (e = t.stateNode, n = t.memoizedProps, r = null, a = Mi, a !== null) switch (a.tag) {
							case 27:
							case 5: r = a.memoizedProps;
						}
						e[ct] = t, e = !!(e.nodeValue === n || r !== null && !0 === r.suppressHydrationWarning || jd(e.nodeValue, n)), e || Li(t, !0);
					} else e = Bd(e).createTextNode(r), e[ct] = t, t.stateNode = e;
				}
				return jc(t), null;
			case 31:
				if (n = t.memoizedState, e === null || e.memoizedState !== null) {
					if (r = Bi(t), n !== null) {
						if (e === null) {
							if (!r) throw Error(i(318));
							if (e = t.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(557));
							e[ct] = t;
						} else Vi(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						jc(t), e = !1;
					} else n = Hi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = n), e = !0;
					if (!e) return t.flags & 256 ? (co(t), t) : (co(t), null);
					if (t.flags & 128) throw Error(i(558));
				}
				return jc(t), null;
			case 13:
				if (r = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (a = Bi(t), r !== null && r.dehydrated !== null) {
						if (e === null) {
							if (!a) throw Error(i(318));
							if (a = t.memoizedState, a = a === null ? null : a.dehydrated, !a) throw Error(i(317));
							a[ct] = t;
						} else Vi(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						jc(t), a = !1;
					} else a = Hi(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = a), a = !0;
					if (!a) return t.flags & 256 ? (co(t), t) : (co(t), null);
				}
				return co(t), t.flags & 128 ? (t.lanes = n, t) : (n = r !== null, e = e !== null && e.memoizedState !== null, n && (r = t.child, a = null, r.alternate !== null && r.alternate.memoizedState !== null && r.alternate.memoizedState.cachePool !== null && (a = r.alternate.memoizedState.cachePool.pool), o = null, r.memoizedState !== null && r.memoizedState.cachePool !== null && (o = r.memoizedState.cachePool.pool), o !== a && (r.flags |= 2048)), n !== e && n && (t.child.flags |= 8192), kc(t, t.updateQueue), jc(t), null);
			case 4: return fe(), e === null && xd(t.stateNode.containerInfo), jc(t), null;
			case 10: return Ji(t.type), jc(t), null;
			case 19:
				if (oe(V), r = t.memoizedState, r === null) return jc(t), null;
				if (a = !!(t.flags & 128), o = r.rendering, o === null) {
					if (a) Ac(r, !1);
					else {
						if (Hl !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
							if (o = lo(e), o !== null) {
								for (t.flags |= 128, Ac(r, !1), e = o.updateQueue, t.updateQueue = e, kc(t, e), t.subtreeFlags = 0, e = n, n = t.child; n !== null;) ui(n, e), n = n.sibling;
								return I(V, V.current & 1 | 2), B && Di(t, r.treeForkCount), t.child;
							}
							e = e.sibling;
						}
						r.tail !== null && De() > $l && (t.flags |= 128, a = !0, Ac(r, !1), t.lanes = 4194304);
					}
				} else {
					if (!a) {
						if (e = lo(o), e !== null) {
							if (t.flags |= 128, a = !0, e = e.updateQueue, t.updateQueue = e, kc(t, e), Ac(r, !0), r.tail === null && r.tailMode === "hidden" && !o.alternate && !B) return jc(t), null;
						} else 2 * De() - r.renderingStartTime > $l && n !== 536870912 && (t.flags |= 128, a = !0, Ac(r, !1), t.lanes = 4194304);
					}
					r.isBackwards ? (o.sibling = t.child, t.child = o) : (e = r.last, e === null ? t.child = o : e.sibling = o, r.last = o);
				}
				return r.tail === null ? (jc(t), null) : (e = r.tail, r.rendering = e, r.tail = e.sibling, r.renderingStartTime = De(), e.sibling = null, n = V.current, I(V, a ? n & 1 | 2 : n & 1), B && Di(t, r.treeForkCount), e);
			case 22:
			case 23: return co(t), to(), r = t.memoizedState !== null, e === null ? r && (t.flags |= 8192) : e.memoizedState !== null !== r && (t.flags |= 8192), r ? n & 536870912 && !(t.flags & 128) && (jc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : jc(t), n = t.updateQueue, n !== null && kc(t, n.retryQueue), n = null, e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), r = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (r = t.memoizedState.cachePool.pool), r !== n && (t.flags |= 2048), e !== null && oe(_a), null;
			case 24: return n = null, e !== null && (n = e.memoizedState.cache), t.memoizedState.cache !== n && (t.flags |= 2048), Ji(oa), jc(t), null;
			case 25: return null;
			case 30: return null;
		}
		throw Error(i(156, t.tag));
	}
	function Nc(e, t) {
		switch (Ai(t), t.tag) {
			case 1: return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return Ji(oa), fe(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 26:
			case 27:
			case 5: return me(t), null;
			case 31:
				if (t.memoizedState !== null) {
					if (co(t), t.alternate === null) throw Error(i(340));
					Vi();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 13:
				if (co(t), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(i(340));
					Vi();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return oe(V), null;
			case 4: return fe(), null;
			case 10: return Ji(t.type), null;
			case 22:
			case 23: return co(t), to(), e !== null && oe(_a), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 24: return Ji(oa), null;
			case 25: return null;
			default: return null;
		}
	}
	function Pc(e, t) {
		switch (Ai(t), t.tag) {
			case 3:
				Ji(oa), fe();
				break;
			case 26:
			case 27:
			case 5:
				me(t);
				break;
			case 4:
				fe();
				break;
			case 31:
				t.memoizedState !== null && co(t);
				break;
			case 13:
				co(t);
				break;
			case 19:
				oe(V);
				break;
			case 10:
				Ji(t.type);
				break;
			case 22:
			case 23:
				co(t), to(), e !== null && oe(_a);
				break;
			case 24: Ji(oa);
		}
	}
	function Fc(e, t) {
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
			Uu(t, t.return, e);
		}
	}
	function Ic(e, t, n) {
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
								Uu(i, c, e);
							}
						}
					}
					r = r.next;
				} while (r !== a);
			}
		} catch (e) {
			Uu(t, t.return, e);
		}
	}
	function Lc(e) {
		var t = e.updateQueue;
		if (t !== null) {
			var n = e.stateNode;
			try {
				Xa(t, n);
			} catch (t) {
				Uu(e, e.return, t);
			}
		}
	}
	function Rc(e, t, n) {
		n.props = zs(e.type, e.memoizedProps), n.state = e.memoizedState;
		try {
			n.componentWillUnmount();
		} catch (n) {
			Uu(e, t, n);
		}
	}
	function zc(e, t) {
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
			Uu(e, t, n);
		}
	}
	function Bc(e, t) {
		var n = e.ref, r = e.refCleanup;
		if (n !== null) {
			if (typeof r == "function") try {
				r();
			} catch (n) {
				Uu(e, t, n);
			} finally {
				e.refCleanup = null, e = e.alternate, e != null && (e.refCleanup = null);
			}
			else if (typeof n == "function") try {
				n(null);
			} catch (n) {
				Uu(e, t, n);
			}
			else n.current = null;
		}
	}
	function Vc(e) {
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
			Uu(e, e.return, t);
		}
	}
	function Hc(e, t, n) {
		try {
			var r = e.stateNode;
			Fd(r, e.type, n, t), r[lt] = t;
		} catch (t) {
			Uu(e, e.return, t);
		}
	}
	function Uc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 26 || e.tag === 27 && Zd(e.type) || e.tag === 4;
	}
	function Wc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || Uc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.tag === 27 && Zd(e.type) || e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Gc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? (n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n).insertBefore(e, t) : (t = n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n, t.appendChild(e), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = tn));
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode, t = null), e = e.child, e !== null)) for (Gc(e, t, n), e = e.sibling; e !== null;) Gc(e, t, n), e = e.sibling;
	}
	function Kc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (r === 27 && Zd(e.type) && (n = e.stateNode), e = e.child, e !== null)) for (Kc(e, t, n), e = e.sibling; e !== null;) Kc(e, t, n), e = e.sibling;
	}
	function qc(e) {
		var t = e.stateNode, n = e.memoizedProps;
		try {
			for (var r = e.type, i = t.attributes; i.length;) t.removeAttributeNode(i[0]);
			Pd(t, r, n), t[ct] = e, t[lt] = n;
		} catch (t) {
			Uu(e, e.return, t);
		}
	}
	var Jc = !1, Yc = !1, Xc = !1, Zc = typeof WeakSet == "function" ? WeakSet : Set, Qc = null;
	function $c(e, t) {
		if (e = e.containerInfo, Rd = sp, e = Er(e), Dr(e)) {
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
		}, sp = !1, Qc = t; Qc !== null;) if (t = Qc, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, Qc = e;
		else for (; Qc !== null;) {
			switch (t = Qc, o = t.alternate, e = t.flags, t.tag) {
				case 0:
					if (e & 4 && (e = t.updateQueue, e = e === null ? null : e.events, e !== null)) for (n = 0; n < e.length; n++) a = e[n], a.ref.impl = a.nextImpl;
					break;
				case 11:
				case 15: break;
				case 1:
					if (e & 1024 && o !== null) {
						e = void 0, n = t, a = o.memoizedProps, o = o.memoizedState, r = n.stateNode;
						try {
							var h = zs(n.type, a);
							e = r.getSnapshotBeforeUpdate(h, o), r.__reactInternalSnapshotBeforeUpdate = e;
						} catch (e) {
							Uu(n, n.return, e);
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
				e.return = t.return, Qc = e;
				break;
			}
			Qc = t.return;
		}
	}
	function el(e, t, n) {
		var r = n.flags;
		switch (n.tag) {
			case 0:
			case 11:
			case 15:
				hl(e, n), r & 4 && Fc(5, n);
				break;
			case 1:
				if (hl(e, n), r & 4) {
					if (e = n.stateNode, t === null) try {
						e.componentDidMount();
					} catch (e) {
						Uu(n, n.return, e);
					}
					else {
						var i = zs(n.type, t.memoizedProps);
						t = t.memoizedState;
						try {
							e.componentDidUpdate(i, t, e.__reactInternalSnapshotBeforeUpdate);
						} catch (e) {
							Uu(n, n.return, e);
						}
					}
				}
				r & 64 && Lc(n), r & 512 && zc(n, n.return);
				break;
			case 3:
				if (hl(e, n), r & 64 && (e = n.updateQueue, e !== null)) {
					if (t = null, n.child !== null) switch (n.child.tag) {
						case 27:
						case 5:
							t = n.child.stateNode;
							break;
						case 1: t = n.child.stateNode;
					}
					try {
						Xa(e, t);
					} catch (e) {
						Uu(n, n.return, e);
					}
				}
				break;
			case 27: t === null && r & 4 && qc(n);
			case 26:
			case 5:
				hl(e, n), t === null && r & 4 && Vc(n), r & 512 && zc(n, n.return);
				break;
			case 12:
				hl(e, n);
				break;
			case 31:
				hl(e, n), r & 4 && ol(e, n);
				break;
			case 13:
				hl(e, n), r & 4 && sl(e, n), r & 64 && (e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null && (n = qu.bind(null, n), sf(e, n))));
				break;
			case 22:
				if (r = n.memoizedState !== null || Jc, !r) {
					t = t !== null && t.memoizedState !== null || Yc, i = Jc;
					var a = Yc;
					Jc = r, (Yc = t) && !a ? _l(e, n, !!(n.subtreeFlags & 8772)) : hl(e, n), Jc = i, Yc = a;
				}
				break;
			case 30: break;
			default: hl(e, n);
		}
	}
	function tl(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, tl(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && gt(t)), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	var nl = null, rl = !1;
	function il(e, t, n) {
		for (n = n.child; n !== null;) al(e, t, n), n = n.sibling;
	}
	function al(e, t, n) {
		if (Le && typeof Le.onCommitFiberUnmount == "function") try {
			Le.onCommitFiberUnmount(Ie, n);
		} catch {}
		switch (n.tag) {
			case 26:
				Yc || Bc(n, t), il(e, t, n), n.memoizedState ? n.memoizedState.count-- : n.stateNode && (n = n.stateNode, n.parentNode.removeChild(n));
				break;
			case 27:
				Yc || Bc(n, t);
				var r = nl, i = rl;
				Zd(n.type) && (nl = n.stateNode, rl = !1), il(e, t, n), pf(n.stateNode), nl = r, rl = i;
				break;
			case 5: Yc || Bc(n, t);
			case 6:
				if (r = nl, i = rl, nl = null, il(e, t, n), nl = r, rl = i, nl !== null) {
					if (rl) try {
						(nl.nodeType === 9 ? nl.body : nl.nodeName === "HTML" ? nl.ownerDocument.body : nl).removeChild(n.stateNode);
					} catch (e) {
						Uu(n, t, e);
					}
					else try {
						nl.removeChild(n.stateNode);
					} catch (e) {
						Uu(n, t, e);
					}
				}
				break;
			case 18:
				nl !== null && (rl ? (e = nl, Qd(e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, n.stateNode), Np(e)) : Qd(nl, n.stateNode));
				break;
			case 4:
				r = nl, i = rl, nl = n.stateNode.containerInfo, rl = !0, il(e, t, n), nl = r, rl = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				Ic(2, n, t), Yc || Ic(4, n, t), il(e, t, n);
				break;
			case 1:
				Yc || (Bc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function" && Rc(n, t, r)), il(e, t, n);
				break;
			case 21:
				il(e, t, n);
				break;
			case 22:
				Yc = (r = Yc) || n.memoizedState !== null, il(e, t, n), Yc = r;
				break;
			default: il(e, t, n);
		}
	}
	function ol(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null))) {
			e = e.dehydrated;
			try {
				Np(e);
			} catch (e) {
				Uu(t, t.return, e);
			}
		}
	}
	function sl(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null && (e = e.dehydrated, e !== null)))) try {
			Np(e);
		} catch (e) {
			Uu(t, t.return, e);
		}
	}
	function cl(e) {
		switch (e.tag) {
			case 31:
			case 13:
			case 19:
				var t = e.stateNode;
				return t === null && (t = e.stateNode = new Zc()), t;
			case 22: return e = e.stateNode, t = e._retryCache, t === null && (t = e._retryCache = new Zc()), t;
			default: throw Error(i(435, e.tag));
		}
	}
	function ll(e, t) {
		var n = cl(e);
		t.forEach(function(t) {
			if (!n.has(t)) {
				n.add(t);
				var r = Ju.bind(null, e, t);
				t.then(r, r);
			}
		});
	}
	function ul(e, t) {
		var n = t.deletions;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var a = n[r], o = e, s = t, c = s;
			a: for (; c !== null;) {
				switch (c.tag) {
					case 27:
						if (Zd(c.type)) {
							nl = c.stateNode, rl = !1;
							break a;
						}
						break;
					case 5:
						nl = c.stateNode, rl = !1;
						break a;
					case 3:
					case 4:
						nl = c.stateNode.containerInfo, rl = !0;
						break a;
				}
				c = c.return;
			}
			if (nl === null) throw Error(i(160));
			al(o, s, a), nl = null, rl = !1, o = a.alternate, o !== null && (o.return = null), a.return = null;
		}
		if (t.subtreeFlags & 13886) for (t = t.child; t !== null;) fl(t, e), t = t.sibling;
	}
	var dl = null;
	function fl(e, t) {
		var n = e.alternate, r = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				ul(t, e), pl(e), r & 4 && (Ic(3, e, e.return), Fc(3, e), Ic(5, e, e.return));
				break;
			case 1:
				ul(t, e), pl(e), r & 512 && (Yc || n === null || Bc(n, n.return)), r & 64 && Jc && (e = e.updateQueue, e !== null && (r = e.callbacks, r !== null && (n = e.shared.hiddenCallbacks, e.shared.hiddenCallbacks = n === null ? r : n.concat(r))));
				break;
			case 26:
				var a = dl;
				if (ul(t, e), pl(e), r & 512 && (Yc || n === null || Bc(n, n.return)), r & 4) {
					var o = n === null ? null : n.memoizedState;
					if (r = e.memoizedState, n === null) {
						if (r === null) {
							if (e.stateNode === null) {
								a: {
									r = e.type, n = e.memoizedProps, a = a.ownerDocument || a;
									b: switch (r) {
										case "title":
											o = a.getElementsByTagName("title")[0], (!o || o[ht] || o[ct] || o.namespaceURI === "http://www.w3.org/2000/svg" || o.hasAttribute("itemprop")) && (o = a.createElement(r), a.head.insertBefore(o, a.querySelector("head > title"))), Pd(o, r, n), o[ct] = e, xt(o), r = o;
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
									o[ct] = e, xt(o), r = o;
								}
								e.stateNode = r;
							} else Hf(a, e.type, e.stateNode);
						} else e.stateNode = If(a, r, e.memoizedProps);
					} else o === r ? r === null && e.stateNode !== null && Hc(e, e.memoizedProps, n.memoizedProps) : (o === null ? n.stateNode !== null && (n = n.stateNode, n.parentNode.removeChild(n)) : o.count--, r === null ? Hf(a, e.type, e.stateNode) : If(a, r, e.memoizedProps));
				}
				break;
			case 27:
				ul(t, e), pl(e), r & 512 && (Yc || n === null || Bc(n, n.return)), n !== null && r & 4 && Hc(e, e.memoizedProps, n.memoizedProps);
				break;
			case 5:
				if (ul(t, e), pl(e), r & 512 && (Yc || n === null || Bc(n, n.return)), e.flags & 32) {
					a = e.stateNode;
					try {
						qt(a, "");
					} catch (t) {
						Uu(e, e.return, t);
					}
				}
				r & 4 && e.stateNode != null && (a = e.memoizedProps, Hc(e, a, n === null ? a : n.memoizedProps)), r & 1024 && (Xc = !0);
				break;
			case 6:
				if (ul(t, e), pl(e), r & 4) {
					if (e.stateNode === null) throw Error(i(162));
					r = e.memoizedProps, n = e.stateNode;
					try {
						n.nodeValue = r;
					} catch (t) {
						Uu(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Bf = null, a = dl, dl = gf(t.containerInfo), ul(t, e), dl = a, pl(e), r & 4 && n !== null && n.memoizedState.isDehydrated) try {
					Np(t.containerInfo);
				} catch (t) {
					Uu(e, e.return, t);
				}
				Xc && (Xc = !1, ml(e));
				break;
			case 4:
				r = dl, dl = gf(e.stateNode.containerInfo), ul(t, e), pl(e), dl = r;
				break;
			case 12:
				ul(t, e), pl(e);
				break;
			case 31:
				ul(t, e), pl(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, ll(e, r)));
				break;
			case 13:
				ul(t, e), pl(e), e.child.flags & 8192 && e.memoizedState !== null != (n !== null && n.memoizedState !== null) && (Zl = De()), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, ll(e, r)));
				break;
			case 22:
				a = e.memoizedState !== null;
				var l = n !== null && n.memoizedState !== null, u = Jc, d = Yc;
				if (Jc = u || a, Yc = d || l, ul(t, e), Yc = d, Jc = u, pl(e), r & 8192) a: for (t = e.stateNode, t._visibility = a ? t._visibility & -2 : t._visibility | 1, a && (n === null || l || Jc || Yc || gl(e)), n = null, t = e;;) {
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
								Uu(l, l.return, e);
							}
						}
					} else if (t.tag === 6) {
						if (n === null) {
							l = t;
							try {
								l.stateNode.nodeValue = a ? "" : l.memoizedProps;
							} catch (e) {
								Uu(l, l.return, e);
							}
						}
					} else if (t.tag === 18) {
						if (n === null) {
							l = t;
							try {
								var m = l.stateNode;
								a ? $d(m, !0) : $d(l.stateNode, !1);
							} catch (e) {
								Uu(l, l.return, e);
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
				r & 4 && (r = e.updateQueue, r !== null && (n = r.retryQueue, n !== null && (r.retryQueue = null, ll(e, n))));
				break;
			case 19:
				ul(t, e), pl(e), r & 4 && (r = e.updateQueue, r !== null && (e.updateQueue = null, ll(e, r)));
				break;
			case 30: break;
			case 21: break;
			default: ul(t, e), pl(e);
		}
	}
	function pl(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				for (var n, r = e.return; r !== null;) {
					if (Uc(r)) {
						n = r;
						break;
					}
					r = r.return;
				}
				if (n == null) throw Error(i(160));
				switch (n.tag) {
					case 27:
						var a = n.stateNode;
						Kc(e, Wc(e), a);
						break;
					case 5:
						var o = n.stateNode;
						n.flags & 32 && (qt(o, ""), n.flags &= -33), Kc(e, Wc(e), o);
						break;
					case 3:
					case 4:
						var s = n.stateNode.containerInfo;
						Gc(e, Wc(e), s);
						break;
					default: throw Error(i(161));
				}
			} catch (t) {
				Uu(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function ml(e) {
		if (e.subtreeFlags & 1024) for (e = e.child; e !== null;) {
			var t = e;
			ml(t), t.tag === 5 && t.flags & 1024 && t.stateNode.reset(), e = e.sibling;
		}
	}
	function hl(e, t) {
		if (t.subtreeFlags & 8772) for (t = t.child; t !== null;) el(e, t.alternate, t), t = t.sibling;
	}
	function gl(e) {
		for (e = e.child; e !== null;) {
			var t = e;
			switch (t.tag) {
				case 0:
				case 11:
				case 14:
				case 15:
					Ic(4, t, t.return), gl(t);
					break;
				case 1:
					Bc(t, t.return);
					var n = t.stateNode;
					typeof n.componentWillUnmount == "function" && Rc(t, t.return, n), gl(t);
					break;
				case 27: pf(t.stateNode);
				case 26:
				case 5:
					Bc(t, t.return), gl(t);
					break;
				case 22:
					t.memoizedState === null && gl(t);
					break;
				case 30:
					gl(t);
					break;
				default: gl(t);
			}
			e = e.sibling;
		}
	}
	function _l(e, t, n) {
		for (n = n && !!(t.subtreeFlags & 8772), t = t.child; t !== null;) {
			var r = t.alternate, i = e, a = t, o = a.flags;
			switch (a.tag) {
				case 0:
				case 11:
				case 15:
					_l(i, a, n), Fc(4, a);
					break;
				case 1:
					if (_l(i, a, n), r = a, i = r.stateNode, typeof i.componentDidMount == "function") try {
						i.componentDidMount();
					} catch (e) {
						Uu(r, r.return, e);
					}
					if (r = a, i = r.updateQueue, i !== null) {
						var s = r.stateNode;
						try {
							var c = i.shared.hiddenCallbacks;
							if (c !== null) for (i.shared.hiddenCallbacks = null, i = 0; i < c.length; i++) Ya(c[i], s);
						} catch (e) {
							Uu(r, r.return, e);
						}
					}
					n && o & 64 && Lc(a), zc(a, a.return);
					break;
				case 27: qc(a);
				case 26:
				case 5:
					_l(i, a, n), n && r === null && o & 4 && Vc(a), zc(a, a.return);
					break;
				case 12:
					_l(i, a, n);
					break;
				case 31:
					_l(i, a, n), n && o & 4 && ol(i, a);
					break;
				case 13:
					_l(i, a, n), n && o & 4 && sl(i, a);
					break;
				case 22:
					a.memoizedState === null && _l(i, a, n), zc(a, a.return);
					break;
				case 30: break;
				default: _l(i, a, n);
			}
			t = t.sibling;
		}
	}
	function vl(e, t) {
		var n = null;
		e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== n && (e != null && e.refCount++, n != null && ca(n));
	}
	function yl(e, t) {
		e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ca(e));
	}
	function bl(e, t, n, r) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) xl(e, t, n, r), t = t.sibling;
	}
	function xl(e, t, n, r) {
		var i = t.flags;
		switch (t.tag) {
			case 0:
			case 11:
			case 15:
				bl(e, t, n, r), i & 2048 && Fc(9, t);
				break;
			case 1:
				bl(e, t, n, r);
				break;
			case 3:
				bl(e, t, n, r), i & 2048 && (e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && ca(e)));
				break;
			case 12:
				if (i & 2048) {
					bl(e, t, n, r), e = t.stateNode;
					try {
						var a = t.memoizedProps, o = a.id, s = a.onPostCommit;
						typeof s == "function" && s(o, t.alternate === null ? "mount" : "update", e.passiveEffectDuration, -0);
					} catch (e) {
						Uu(t, t.return, e);
					}
				} else bl(e, t, n, r);
				break;
			case 31:
				bl(e, t, n, r);
				break;
			case 13:
				bl(e, t, n, r);
				break;
			case 23: break;
			case 22:
				a = t.stateNode, o = t.alternate, t.memoizedState === null ? a._visibility & 2 ? bl(e, t, n, r) : (a._visibility |= 2, Sl(e, t, n, r, !!(t.subtreeFlags & 10256) || !1)) : a._visibility & 2 ? bl(e, t, n, r) : Cl(e, t), i & 2048 && vl(o, t);
				break;
			case 24:
				bl(e, t, n, r), i & 2048 && yl(t.alternate, t);
				break;
			default: bl(e, t, n, r);
		}
	}
	function Sl(e, t, n, r, i) {
		for (i = i && (!!(t.subtreeFlags & 10256) || !1), t = t.child; t !== null;) {
			var a = e, o = t, s = n, c = r, l = o.flags;
			switch (o.tag) {
				case 0:
				case 11:
				case 15:
					Sl(a, o, s, c, i), Fc(8, o);
					break;
				case 23: break;
				case 22:
					var u = o.stateNode;
					o.memoizedState === null ? (u._visibility |= 2, Sl(a, o, s, c, i)) : u._visibility & 2 ? Sl(a, o, s, c, i) : Cl(a, o), i && l & 2048 && vl(o.alternate, o);
					break;
				case 24:
					Sl(a, o, s, c, i), i && l & 2048 && yl(o.alternate, o);
					break;
				default: Sl(a, o, s, c, i);
			}
			t = t.sibling;
		}
	}
	function Cl(e, t) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) {
			var n = e, r = t, i = r.flags;
			switch (r.tag) {
				case 22:
					Cl(n, r), i & 2048 && vl(r.alternate, r);
					break;
				case 24:
					Cl(n, r), i & 2048 && yl(r.alternate, r);
					break;
				default: Cl(n, r);
			}
			t = t.sibling;
		}
	}
	var wl = 8192;
	function Tl(e, t, n) {
		if (e.subtreeFlags & wl) for (e = e.child; e !== null;) El(e, t, n), e = e.sibling;
	}
	function El(e, t, n) {
		switch (e.tag) {
			case 26:
				Tl(e, t, n), e.flags & wl && e.memoizedState !== null && Gf(n, dl, e.memoizedState, e.memoizedProps);
				break;
			case 5:
				Tl(e, t, n);
				break;
			case 3:
			case 4:
				var r = dl;
				dl = gf(e.stateNode.containerInfo), Tl(e, t, n), dl = r;
				break;
			case 22:
				e.memoizedState === null && (r = e.alternate, r !== null && r.memoizedState !== null ? (r = wl, wl = 16777216, Tl(e, t, n), wl = r) : Tl(e, t, n));
				break;
			default: Tl(e, t, n);
		}
	}
	function Dl(e) {
		var t = e.alternate;
		if (t !== null && (e = t.child, e !== null)) {
			t.child = null;
			do
				t = e.sibling, e.sibling = null, e = t;
			while (e !== null);
		}
	}
	function Ol(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				Qc = r, jl(r, e);
			}
			Dl(e);
		}
		if (e.subtreeFlags & 10256) for (e = e.child; e !== null;) kl(e), e = e.sibling;
	}
	function kl(e) {
		switch (e.tag) {
			case 0:
			case 11:
			case 15:
				Ol(e), e.flags & 2048 && Ic(9, e, e.return);
				break;
			case 3:
				Ol(e);
				break;
			case 12:
				Ol(e);
				break;
			case 22:
				var t = e.stateNode;
				e.memoizedState !== null && t._visibility & 2 && (e.return === null || e.return.tag !== 13) ? (t._visibility &= -3, Al(e)) : Ol(e);
				break;
			default: Ol(e);
		}
	}
	function Al(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				Qc = r, jl(r, e);
			}
			Dl(e);
		}
		for (e = e.child; e !== null;) {
			switch (t = e, t.tag) {
				case 0:
				case 11:
				case 15:
					Ic(8, t, t.return), Al(t);
					break;
				case 22:
					n = t.stateNode, n._visibility & 2 && (n._visibility &= -3, Al(t));
					break;
				default: Al(t);
			}
			e = e.sibling;
		}
	}
	function jl(e, t) {
		for (; Qc !== null;) {
			var n = Qc;
			switch (n.tag) {
				case 0:
				case 11:
				case 15:
					Ic(8, n, t);
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
			if (r = n.child, r !== null) r.return = n, Qc = r;
			else a: for (n = e; Qc !== null;) {
				r = Qc;
				var i = r.sibling, a = r.return;
				if (tl(r), r === n) {
					Qc = null;
					break a;
				}
				if (i !== null) {
					i.return = a, Qc = i;
					break a;
				}
				Qc = a;
			}
		}
	}
	var Ml = {
		getCacheForType: function(e) {
			var t = ea(oa), n = t.data.get(e);
			return n === void 0 && (n = e(), t.data.set(e, n)), n;
		},
		cacheSignal: function() {
			return ea(oa).controller.signal;
		}
	}, Nl = typeof WeakMap == "function" ? WeakMap : Map, Pl = 0, Fl = null, Z = null, Q = 0, Il = 0, Ll = null, Rl = !1, zl = !1, Bl = !1, Vl = 0, Hl = 0, Ul = 0, Wl = 0, Gl = 0, Kl = 0, ql = 0, Jl = null, Yl = null, Xl = !1, Zl = 0, Ql = 0, $l = Infinity, eu = null, tu = null, nu = 0, ru = null, iu = null, au = 0, ou = 0, su = null, cu = null, lu = 0, uu = null;
	function du() {
		return Pl & 2 && Q !== 0 ? Q & -Q : P.T === null ? at() : ud();
	}
	function fu() {
		if (Kl === 0) {
			if (!(Q & 536870912) || B) {
				var e = We;
				We <<= 1, !(We & 3932160) && (We = 262144), Kl = e;
			} else Kl = 536870912;
		}
		return e = no.current, e !== null && (e.flags |= 32), Kl;
	}
	function pu(e, t, n) {
		(e === Fl && (Il === 2 || Il === 9) || e.cancelPendingCommit !== null) && (bu(e, 0), _u(e, Q, Kl, !1)), Qe(e, n), (!(Pl & 2) || e !== Fl) && (e === Fl && (!(Pl & 2) && (Wl |= n), Hl === 4 && _u(e, Q, Kl, !1)), nd(e));
	}
	function mu(e, t, n) {
		if (Pl & 6) throw Error(i(327));
		var r = !n && !(t & 127) && (t & e.expiredLanes) === 0 || Je(e, t), a = r ? Ou(e, t) : Eu(e, t, !0), o = r;
		do {
			if (a === 0) {
				zl && !r && _u(e, t, 0, !1);
				break;
			}
			if (n = e.current.alternate, o && !gu(n)) {
				a = Eu(e, t, !1), o = !1;
				continue;
			}
			if (a === 2) {
				if (o = t, e.errorRecoveryDisabledLanes & o) var s = 0;
				else s = e.pendingLanes & -536870913, s = s === 0 ? s & 536870912 ? 536870912 : 0 : s;
				if (s !== 0) {
					t = s;
					a: {
						var c = e;
						a = Jl;
						var l = c.current.memoizedState.isDehydrated;
						if (l && (bu(c, s).flags |= 256), s = Eu(c, s, !1), s !== 2) {
							if (Bl && !l) {
								c.errorRecoveryDisabledLanes |= o, Wl |= o, a = 4;
								break a;
							}
							o = Yl, Yl = a, o !== null && (Yl === null ? Yl = o : Yl.push.apply(Yl, o));
						}
						a = s;
					}
					if (o = !1, a !== 2) continue;
				}
			}
			if (a === 1) {
				bu(e, 0), _u(e, t, 0, !0);
				break;
			}
			a: {
				switch (r = e, o = a, o) {
					case 0:
					case 1: throw Error(i(345));
					case 4: if ((t & 4194048) !== t) break;
					case 6:
						_u(r, t, Kl, !Rl);
						break a;
					case 2:
						Yl = null;
						break;
					case 3:
					case 5: break;
					default: throw Error(i(329));
				}
				if ((t & 62914560) === t && (a = Zl + 300 - De(), 10 < a)) {
					if (_u(r, t, Kl, !Rl), qe(r, 0, !0) !== 0) break a;
					au = t, r.timeoutHandle = Kd(hu.bind(null, r, n, Yl, eu, Xl, t, Kl, Wl, ql, Rl, o, "Throttled", -0, 0), a);
					break a;
				}
				hu(r, n, Yl, eu, Xl, t, Kl, Wl, ql, Rl, o, null, -0, 0);
			}
			break;
		} while (1);
		nd(e);
	}
	function hu(e, t, n, r, i, a, o, s, c, l, u, d, f, p) {
		if (e.timeoutHandle = -1, d = t.subtreeFlags, d & 8192 || (d & 16785408) == 16785408) {
			d = {
				stylesheets: null,
				count: 0,
				imgCount: 0,
				imgBytes: 0,
				suspenseyImages: [],
				waitingForImages: !0,
				waitingForViewTransition: !1,
				unsuspend: tn
			}, El(t, a, d);
			var m = (a & 62914560) === a ? Zl - De() : (a & 4194048) === a ? Ql - De() : 0;
			if (m = qf(d, m), m !== null) {
				au = a, e.cancelPendingCommit = m(Fu.bind(null, e, t, a, n, r, i, o, s, c, u, d, null, f, p)), _u(e, a, o, !l);
				return;
			}
		}
		Fu(e, t, a, n, r, i, o, s, c);
	}
	function gu(e) {
		for (var t = e;;) {
			var n = t.tag;
			if ((n === 0 || n === 11 || n === 15) && t.flags & 16384 && (n = t.updateQueue, n !== null && (n = n.stores, n !== null))) for (var r = 0; r < n.length; r++) {
				var i = n[r], a = i.getSnapshot;
				i = i.value;
				try {
					if (!xr(a(), i)) return !1;
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
	function _u(e, t, n, r) {
		t &= ~Gl, t &= ~Wl, e.suspendedLanes |= t, e.pingedLanes &= ~t, r && (e.warmLanes |= t), r = e.expirationTimes;
		for (var i = t; 0 < i;) {
			var a = 31 - ze(i), o = 1 << a;
			r[a] = -1, i &= ~o;
		}
		n !== 0 && et(e, n, t);
	}
	function vu() {
		return Pl & 6 ? !0 : (rd(0, !1), !1);
	}
	function yu() {
		if (Z !== null) {
			if (Il === 0) var e = Z.return;
			else e = Z, Ki = Gi = null, J(e), ja = null, Ma = 0, e = Z;
			for (; e !== null;) Pc(e.alternate, e), e = e.return;
			Z = null;
		}
	}
	function bu(e, t) {
		var n = e.timeoutHandle;
		n !== -1 && (e.timeoutHandle = -1, qd(n)), n = e.cancelPendingCommit, n !== null && (e.cancelPendingCommit = null, n()), au = 0, yu(), Fl = e, Z = n = li(e.current, null), Q = t, Il = 0, Ll = null, Rl = !1, zl = Je(e, t), Bl = !1, ql = Kl = Gl = Wl = Ul = Hl = 0, Yl = Jl = null, Xl = !1, t & 8 && (t |= t & 32);
		var r = e.entangledLanes;
		if (r !== 0) for (e = e.entanglements, r &= t; 0 < r;) {
			var i = 31 - ze(r), a = 1 << i;
			t |= e[i], r &= ~a;
		}
		return Vl = t, $r(), n;
	}
	function xu(e, t) {
		H = null, P.H = js, t === xa || t === Ca ? (t = ka(), Il = 3) : t === Sa ? (t = ka(), Il = 4) : Il = t === Ys ? 8 : typeof t == "object" && t && typeof t.then == "function" ? 6 : 1, Ll = t, Z === null && (Hl = 1, Us(e, _i(t, e.current)));
	}
	function Su() {
		var e = no.current;
		return e === null ? !0 : (Q & 4194048) === Q ? ro === null : (Q & 62914560) === Q || Q & 536870912 ? e === ro : !1;
	}
	function Cu() {
		var e = P.H;
		return P.H = js, e === null ? js : e;
	}
	function wu() {
		var e = P.A;
		return P.A = Ml, e;
	}
	function Tu() {
		Hl = 4, Rl || (Q & 4194048) !== Q && no.current !== null || (zl = !0), !(Ul & 134217727) && !(Wl & 134217727) || Fl === null || _u(Fl, Q, Kl, !1);
	}
	function Eu(e, t, n) {
		var r = Pl;
		Pl |= 2;
		var i = Cu(), a = wu();
		(Fl !== e || Q !== t) && (eu = null, bu(e, t)), t = !1;
		var o = Hl;
		a: do
			try {
				if (Il !== 0 && Z !== null) {
					var s = Z, c = Ll;
					switch (Il) {
						case 8:
							yu(), o = 6;
							break a;
						case 3:
						case 2:
						case 9:
						case 6:
							no.current === null && (t = !0);
							var l = Il;
							if (Il = 0, Ll = null, Mu(e, s, c, l), n && zl) {
								o = 0;
								break a;
							}
							break;
						default: l = Il, Il = 0, Ll = null, Mu(e, s, c, l);
					}
				}
				Du(), o = Hl;
				break;
			} catch (t) {
				xu(e, t);
			}
		while (1);
		return t && e.shellSuspendCounter++, Ki = Gi = null, Pl = r, P.H = i, P.A = a, Z === null && (Fl = null, Q = 0, $r()), o;
	}
	function Du() {
		for (; Z !== null;) Au(Z);
	}
	function Ou(e, t) {
		var n = Pl;
		Pl |= 2;
		var r = Cu(), a = wu();
		Fl !== e || Q !== t ? (eu = null, $l = De() + 500, bu(e, t)) : zl = Je(e, t);
		a: do
			try {
				if (Il !== 0 && Z !== null) {
					t = Z;
					var o = Ll;
					b: switch (Il) {
						case 1:
							Il = 0, Ll = null, Mu(e, t, o, 1);
							break;
						case 2:
						case 9:
							if (Ta(o)) {
								Il = 0, Ll = null, ju(t);
								break;
							}
							t = function() {
								Il !== 2 && Il !== 9 || Fl !== e || (Il = 7), nd(e);
							}, o.then(t, t);
							break a;
						case 3:
							Il = 7;
							break a;
						case 4:
							Il = 5;
							break a;
						case 7:
							Ta(o) ? (Il = 0, Ll = null, ju(t)) : (Il = 0, Ll = null, Mu(e, t, o, 7));
							break;
						case 5:
							var s = null;
							switch (Z.tag) {
								case 26: s = Z.memoizedState;
								case 5:
								case 27:
									var c = Z;
									if (s ? Wf(s) : c.stateNode.complete) {
										Il = 0, Ll = null;
										var l = c.sibling;
										if (l !== null) Z = l;
										else {
											var u = c.return;
											u === null ? Z = null : (Z = u, Nu(u));
										}
										break b;
									}
							}
							Il = 0, Ll = null, Mu(e, t, o, 5);
							break;
						case 6:
							Il = 0, Ll = null, Mu(e, t, o, 6);
							break;
						case 8:
							yu(), Hl = 6;
							break a;
						default: throw Error(i(462));
					}
				}
				ku();
				break;
			} catch (t) {
				xu(e, t);
			}
		while (1);
		return Ki = Gi = null, P.H = r, P.A = a, Pl = n, Z === null ? (Fl = null, Q = 0, $r(), Hl) : 0;
	}
	function ku() {
		for (; Z !== null && !Te();) Au(Z);
	}
	function Au(e) {
		var t = Tc(e.alternate, e, Vl);
		e.memoizedProps = e.pendingProps, t === null ? Nu(e) : Z = t;
	}
	function ju(e) {
		var t = e, n = t.alternate;
		switch (t.tag) {
			case 15:
			case 0:
				t = lc(n, t, t.pendingProps, t.type, void 0, Q);
				break;
			case 11:
				t = lc(n, t, t.pendingProps, t.type.render, t.ref, Q);
				break;
			case 5: J(t);
			default: Pc(n, t), t = Z = ui(t, Vl), t = Tc(n, t, Vl);
		}
		e.memoizedProps = e.pendingProps, t === null ? Nu(e) : Z = t;
	}
	function Mu(e, t, n, r) {
		Ki = Gi = null, J(t), ja = null, Ma = 0;
		var i = t.return;
		try {
			if (Js(e, i, t, n, Q)) {
				Hl = 1, Us(e, _i(n, e.current)), Z = null;
				return;
			}
		} catch (t) {
			if (i !== null) throw Z = i, t;
			Hl = 1, Us(e, _i(n, e.current)), Z = null;
			return;
		}
		t.flags & 32768 ? (B || r === 1 ? e = !0 : zl || Q & 536870912 ? e = !1 : (Rl = e = !0, (r === 2 || r === 9 || r === 3 || r === 6) && (r = no.current, r !== null && r.tag === 13 && (r.flags |= 16384))), Pu(t, e)) : Nu(t);
	}
	function Nu(e) {
		var t = e;
		do {
			if (t.flags & 32768) {
				Pu(t, Rl);
				return;
			}
			e = t.return;
			var n = Mc(t.alternate, t, Vl);
			if (n !== null) {
				Z = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				Z = t;
				return;
			}
			Z = t = e;
		} while (t !== null);
		Hl === 0 && (Hl = 5);
	}
	function Pu(e, t) {
		do {
			var n = Nc(e.alternate, e);
			if (n !== null) {
				n.flags &= 32767, Z = n;
				return;
			}
			if (n = e.return, n !== null && (n.flags |= 32768, n.subtreeFlags = 0, n.deletions = null), !t && (e = e.sibling, e !== null)) {
				Z = e;
				return;
			}
			Z = e = n;
		} while (e !== null);
		Hl = 6, Z = null;
	}
	function Fu(e, t, n, r, a, o, s, c, l) {
		e.cancelPendingCommit = null;
		do
			Bu();
		while (nu !== 0);
		if (Pl & 6) throw Error(i(327));
		if (t !== null) {
			if (t === e.current) throw Error(i(177));
			if (o = t.lanes | t.childLanes, o |= Qr, $e(e, n, o, s, c, l), e === Fl && (Z = Fl = null, Q = 0), iu = t, ru = e, au = n, ou = o, su = a, cu = r, t.subtreeFlags & 10256 || t.flags & 10256 ? (e.callbackNode = null, e.callbackPriority = 0, Yu(je, function() {
				return Vu(), null;
			})) : (e.callbackNode = null, e.callbackPriority = 0), r = !!(t.flags & 13878), t.subtreeFlags & 13878 || r) {
				r = P.T, P.T = null, a = F.p, F.p = 2, s = Pl, Pl |= 4;
				try {
					$c(e, t, n);
				} finally {
					Pl = s, F.p = a, P.T = r;
				}
			}
			nu = 1, Iu(), Lu(), Ru();
		}
	}
	function Iu() {
		if (nu === 1) {
			nu = 0;
			var e = ru, t = iu, n = !!(t.flags & 13878);
			if (t.subtreeFlags & 13878 || n) {
				n = P.T, P.T = null;
				var r = F.p;
				F.p = 2;
				var i = Pl;
				Pl |= 4;
				try {
					fl(t, e);
					var a = zd, o = Er(e.containerInfo), s = a.focusedElem, c = a.selectionRange;
					if (o !== s && s && s.ownerDocument && Tr(s.ownerDocument.documentElement, s)) {
						if (c !== null && Dr(s)) {
							var l = c.start, u = c.end;
							if (u === void 0 && (u = l), "selectionStart" in s) s.selectionStart = l, s.selectionEnd = Math.min(u, s.value.length);
							else {
								var d = s.ownerDocument || document, f = d && d.defaultView || window;
								if (f.getSelection) {
									var p = f.getSelection(), m = s.textContent.length, h = Math.min(c.start, m), g = c.end === void 0 ? h : Math.min(c.end, m);
									!p.extend && h > g && (o = g, g = h, h = o);
									var _ = wr(s, h), v = wr(s, g);
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
					Pl = i, F.p = r, P.T = n;
				}
			}
			e.current = t, nu = 2;
		}
	}
	function Lu() {
		if (nu === 2) {
			nu = 0;
			var e = ru, t = iu, n = !!(t.flags & 8772);
			if (t.subtreeFlags & 8772 || n) {
				n = P.T, P.T = null;
				var r = F.p;
				F.p = 2;
				var i = Pl;
				Pl |= 4;
				try {
					el(e, t.alternate, t);
				} finally {
					Pl = i, F.p = r, P.T = n;
				}
			}
			nu = 3;
		}
	}
	function Ru() {
		if (nu === 4 || nu === 3) {
			nu = 0, Ee();
			var e = ru, t = iu, n = au, r = cu;
			t.subtreeFlags & 10256 || t.flags & 10256 ? nu = 5 : (nu = 0, iu = ru = null, zu(e, e.pendingLanes));
			var i = e.pendingLanes;
			if (i === 0 && (tu = null), it(n), t = t.stateNode, Le && typeof Le.onCommitFiberRoot == "function") try {
				Le.onCommitFiberRoot(Ie, t, void 0, (t.current.flags & 128) == 128);
			} catch {}
			if (r !== null) {
				t = P.T, i = F.p, F.p = 2, P.T = null;
				try {
					for (var a = e.onRecoverableError, o = 0; o < r.length; o++) {
						var s = r[o];
						a(s.value, { componentStack: s.stack });
					}
				} finally {
					P.T = t, F.p = i;
				}
			}
			au & 3 && Bu(), nd(e), i = e.pendingLanes, n & 261930 && i & 42 ? e === uu ? lu++ : (lu = 0, uu = e) : lu = 0, rd(0, !1);
		}
	}
	function zu(e, t) {
		(e.pooledCacheLanes &= t) === 0 && (t = e.pooledCache, t != null && (e.pooledCache = null, ca(t)));
	}
	function Bu() {
		return Iu(), Lu(), Ru(), Vu();
	}
	function Vu() {
		if (nu !== 5) return !1;
		var e = ru, t = ou;
		ou = 0;
		var n = it(au), r = P.T, a = F.p;
		try {
			F.p = 32 > n ? 32 : n, P.T = null, n = su, su = null;
			var o = ru, s = au;
			if (nu = 0, iu = ru = null, au = 0, Pl & 6) throw Error(i(331));
			var c = Pl;
			if (Pl |= 4, kl(o.current), xl(o, o.current, s, n), Pl = c, rd(0, !1), Le && typeof Le.onPostCommitFiberRoot == "function") try {
				Le.onPostCommitFiberRoot(Ie, o);
			} catch {}
			return !0;
		} finally {
			F.p = a, P.T = r, zu(e, t);
		}
	}
	function Hu(e, t, n) {
		t = _i(n, t), t = Gs(e.stateNode, t, 2), e = Ua(e, t, 2), e !== null && (Qe(e, 2), nd(e));
	}
	function Uu(e, t, n) {
		if (e.tag === 3) Hu(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Hu(t, e, n);
				break;
			}
			if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (tu === null || !tu.has(r))) {
					e = _i(n, e), n = Ks(2), r = Ua(t, n, 2), r !== null && (qs(n, r, t, e), Qe(r, 2), nd(r));
					break;
				}
			}
			t = t.return;
		}
	}
	function Wu(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Nl();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (Bl = !0, i.add(n), e = Gu.bind(null, e, t, n), t.then(e, e));
	}
	function Gu(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), e.pingedLanes |= e.suspendedLanes & n, e.warmLanes &= ~n, Fl === e && (Q & n) === n && (Hl === 4 || Hl === 3 && (Q & 62914560) === Q && 300 > De() - Zl ? !(Pl & 2) && bu(e, 0) : Gl |= n, ql === Q && (ql = 0)), nd(e);
	}
	function Ku(e, t) {
		t === 0 && (t = Xe()), e = ni(e, t), e !== null && (Qe(e, t), nd(e));
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
		return Ce(e, t);
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
								a = (1 << 31 - ze(42 | e) + 1) - 1, a &= i & ~(o & ~s), a = a & 201326741 ? a & 201326741 | 1 : a ? a | 2 : 0;
							}
							a !== 0 && (n = !0, cd(r, a));
						} else a = Q, a = qe(r, r === Fl ? a : 0, r.cancelPendingCommit !== null || r.timeoutHandle !== -1), !(a & 3) || Je(r, a) || (n = !0, cd(r, a));
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
		for (var t = De(), n = null, r = Xu; r !== null;) {
			var i = r.next, a = od(r, t);
			a === 0 ? (r.next = null, n === null ? Xu = i : n.next = i, i === null && (Zu = n)) : (n = r, (e !== 0 || a & 3) && ($u = !0)), r = i;
		}
		nu !== 0 && nu !== 5 || rd(e, !1), td !== 0 && (td = 0);
	}
	function od(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes & -62914561; 0 < a;) {
			var o = 31 - ze(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = Ye(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
		if (t = Fl, n = Q, n = qe(e, e === t ? n : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r = e.callbackNode, n === 0 || e === t && (Il === 2 || Il === 9) || e.cancelPendingCommit !== null) return r !== null && r !== null && we(r), e.callbackNode = null, e.callbackPriority = 0;
		if (!(n & 3) || Je(e, n)) {
			if (t = n & -n, t === e.callbackPriority) return t;
			switch (r !== null && we(r), it(n)) {
				case 2:
				case 8:
					n = Ae;
					break;
				case 32:
					n = je;
					break;
				case 268435456:
					n = Ne;
					break;
				default: n = je;
			}
			return r = sd.bind(null, e), n = Ce(n, r), e.callbackPriority = t, e.callbackNode = n, t;
		}
		return r !== null && r !== null && we(r), e.callbackPriority = 2, e.callbackNode = null, 2;
	}
	function sd(e, t) {
		if (nu !== 0 && nu !== 5) return e.callbackNode = null, e.callbackPriority = 0, null;
		var n = e.callbackNode;
		if (Bu() && e.callbackNode !== n) return null;
		var r = Q;
		return r = qe(e, e === Fl ? r : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r === 0 ? null : (mu(e, r, t), od(e, De()), e.callbackNode != null && e.callbackNode === n ? sd.bind(null, e) : null);
	}
	function cd(e, t) {
		if (Bu()) return null;
		mu(e, t, !0);
	}
	function ld() {
		Yd(function() {
			Pl & 6 ? Ce(ke, id) : ad();
		});
	}
	function ud() {
		if (td === 0) {
			var e = da;
			e === 0 && (e = Ue, Ue <<= 1, !(Ue & 261888) && (Ue = 256)), td = e;
		}
		return td;
	}
	function dd(e) {
		return e == null || typeof e == "symbol" || typeof e == "boolean" ? null : typeof e == "function" ? e : en("" + e);
	}
	function fd(e, t) {
		var n = t.ownerDocument.createElement("input");
		return n.name = t.name, n.value = t.value, e.id && n.setAttribute("form", e.id), t.parentNode.insertBefore(n, t), e = new FormData(e), n.parentNode.removeChild(n), e;
	}
	function pd(e, t, n, r, i) {
		if (t === "submit" && n && n.stateNode === i) {
			var a = dd((i[lt] || null).action), o = r.submitter;
			o && (t = (t = o[lt] || null) ? dd(t.formAction) : o.getAttribute("formAction"), t !== null && (a = t, o = null));
			var s = new Cn("action", "action", null, r, i);
			e.push({
				event: s,
				listeners: [{
					instance: null,
					listener: function() {
						if (r.defaultPrevented) {
							if (td !== 0) {
								var e = o ? fd(i, o) : new FormData(i);
								_s(n, {
									pending: !0,
									data: e,
									method: i.method,
									action: a
								}, null, e);
							}
						} else typeof a == "function" && (s.preventDefault(), e = o ? fd(i, o) : new FormData(i), _s(n, {
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
	for (var md = 0; md < qr.length; md++) {
		var hd = qr[md];
		Jr(hd.toLowerCase(), "on" + (hd[0].toUpperCase() + hd.slice(1)));
	}
	Jr(zr, "onAnimationEnd"), Jr(Br, "onAnimationIteration"), Jr(Vr, "onAnimationStart"), Jr("dblclick", "onDoubleClick"), Jr("focusin", "onFocus"), Jr("focusout", "onBlur"), Jr(Hr, "onTransitionRun"), Jr(Ur, "onTransitionStart"), Jr(Wr, "onTransitionCancel"), Jr(Gr, "onTransitionEnd"), Tt("onMouseEnter", ["mouseout", "mouseover"]), Tt("onMouseLeave", ["mouseout", "mouseover"]), Tt("onPointerEnter", ["pointerout", "pointerover"]), Tt("onPointerLeave", ["pointerout", "pointerover"]), wt("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), wt("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), wt("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), wt("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), wt("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), wt("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
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
						Yr(e);
					}
					i.currentTarget = null, a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						Yr(e);
					}
					i.currentTarget = null, a = c;
				}
			}
		}
	}
	function $(e, t) {
		var n = t[dt];
		n === void 0 && (n = t[dt] = /* @__PURE__ */ new Set());
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
			e[bd] = !0, St.forEach(function(t) {
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
		n = i.bind(null, t, n, e), i = void 0, !fn || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
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
					if (s = _t(c), s === null) return;
					if (l = s.tag, l === 5 || l === 6 || l === 26 || l === 27) {
						r = a = s;
						continue a;
					}
					c = c.parentNode;
				}
			}
			r = r.return;
		}
		ln(function() {
			var r = a, i = rn(n), s = [];
			a: {
				var c = Kr.get(e);
				if (c !== void 0) {
					var l = Cn, u = e;
					switch (e) {
						case "keypress": if (vn(n) === 0) break a;
						case "keydown":
						case "keyup":
							l = Bn;
							break;
						case "focusin":
							u = "focus", l = Mn;
							break;
						case "focusout":
							u = "blur", l = Mn;
							break;
						case "beforeblur":
						case "afterblur":
							l = Mn;
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
							l = An;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							l = jn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							l = Hn;
							break;
						case zr:
						case Br:
						case Vr:
							l = L;
							break;
						case Gr:
							l = Un;
							break;
						case "scroll":
						case "scrollend":
							l = Tn;
							break;
						case "wheel":
							l = Wn;
							break;
						case "copy":
						case "cut":
						case "paste":
							l = Nn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup":
							l = Vn;
							break;
						case "toggle":
						case "beforetoggle": l = R;
					}
					var d = !!(t & 4), f = !d && (e === "scroll" || e === "scrollend"), p = d ? c === null ? null : c + "Capture" : c;
					d = [];
					for (var m = r, h; m !== null;) {
						var g = m;
						if (h = g.stateNode, g = g.tag, g !== 5 && g !== 26 && g !== 27 || h === null || p === null || (g = un(m, p), g != null && d.push(wd(m, g, h))), f) break;
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
					if (c = e === "mouseover" || e === "pointerover", l = e === "mouseout" || e === "pointerout", c && n !== nn && (u = n.relatedTarget || n.fromElement) && (_t(u) || u[ut])) break a;
					if ((l || c) && (c = i.window === i ? i : (c = i.ownerDocument) ? c.defaultView || c.parentWindow : window, l ? (u = n.relatedTarget || n.toElement, l = r, u = u ? _t(u) : null, u !== null && (f = o(u), d = u.tag, u !== f || d !== 5 && d !== 27 && d !== 6) && (u = null)) : (l = null, u = r), l !== u)) {
						if (d = An, g = "onMouseLeave", p = "onMouseEnter", m = "mouse", (e === "pointerout" || e === "pointerover") && (d = Vn, g = "onPointerLeave", p = "onPointerEnter", m = "pointer"), f = l == null ? c : yt(l), h = u == null ? c : yt(u), c = new d(g, m + "leave", l, n, i), c.target = f, c.relatedTarget = h, g = null, _t(i) === r && (d = new d(p, m + "enter", u, n, i), d.target = h, d.relatedTarget = f, g = d), f = g, l && u) b: {
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
					if (c = r ? yt(r) : window, l = c.nodeName && c.nodeName.toLowerCase(), l === "select" || l === "input" && c.type === "file") var v = lr;
					else if (ir(c)) {
						if (ur) v = yr;
						else {
							v = _r;
							var y = gr;
						}
					} else l = c.nodeName, !l || l.toLowerCase() !== "input" || c.type !== "checkbox" && c.type !== "radio" ? r && Zt(r.elementType) && (v = lr) : v = vr;
					if (v && (v = v(e, r))) {
						ar(s, v, n, i);
						break a;
					}
					y && y(e, c, r), e === "focusout" && r && c.type === "number" && r.memoizedProps.value != null && Ut(c, "number", c.value);
				}
				switch (y = r ? yt(r) : window, e) {
					case "focusin":
						(ir(y) || y.contentEditable === "true") && (kr = y, Ar = r, jr = null);
						break;
					case "focusout":
						jr = Ar = kr = null;
						break;
					case "mousedown":
						Mr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Mr = !1, Nr(s, n, i);
						break;
					case "selectionchange": if (Or) break;
					case "keydown":
					case "keyup": Nr(s, n, i);
				}
				var b;
				if (Kn) b: {
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
				else er ? Qn(e, n) && (x = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (x = "onCompositionStart");
				x && (Yn && n.locale !== "ko" && (er || x !== "onCompositionStart" ? x === "onCompositionEnd" && er && (b = _n()) : (mn = i, hn = "value" in mn ? mn.value : mn.textContent, er = !0)), y = Td(r, x), 0 < y.length && (x = new Pn(x, e, null, n, i), s.push({
					event: x,
					listeners: y
				}), b ? x.data = b : (b = $n(n), b !== null && (x.data = b)))), (b = Jn ? tr(e, n) : nr(e, n)) && (x = Td(r, "onBeforeInput"), 0 < x.length && (y = new Pn("onBeforeInput", "beforeinput", null, n, i), s.push({
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
			if (i = i.tag, i !== 5 && i !== 26 && i !== 27 || a === null || (i = un(e, n), i != null && r.unshift(wd(e, i, a)), i = un(e, t), i != null && r.push(wd(e, i, a))), e.tag === 3) return r;
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
			s !== 5 && s !== 26 && s !== 27 || l === null || (c = l, i ? (l = un(n, a), l != null && o.unshift(wd(n, l, c))) : i || (l = un(n, a), l != null && o.push(wd(n, l, c)))), n = n.return;
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
				typeof r == "string" ? t === "body" || t === "textarea" && r === "" || qt(e, r) : (typeof r == "number" || typeof r == "bigint") && t !== "body" && qt(e, "" + r);
				break;
			case "className":
				jt(e, "class", r);
				break;
			case "tabIndex":
				jt(e, "tabindex", r);
				break;
			case "dir":
			case "role":
			case "viewBox":
			case "width":
			case "height":
				jt(e, n, r);
				break;
			case "style":
				Xt(e, r, o);
				break;
			case "data": if (t !== "object") {
				jt(e, "data", r);
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
				r = en("" + r), e.setAttribute(n, r);
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
				r = en("" + r), e.setAttribute(n, r);
				break;
			case "onClick":
				r != null && (e.onclick = tn);
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
				n = en("" + r), e.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", n);
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
				$("beforetoggle", e), $("toggle", e), At(e, "popover", r);
				break;
			case "xlinkActuate":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:actuate", r);
				break;
			case "xlinkArcrole":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:arcrole", r);
				break;
			case "xlinkRole":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:role", r);
				break;
			case "xlinkShow":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:show", r);
				break;
			case "xlinkTitle":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:title", r);
				break;
			case "xlinkType":
				Mt(e, "http://www.w3.org/1999/xlink", "xlink:type", r);
				break;
			case "xmlBase":
				Mt(e, "http://www.w3.org/XML/1998/namespace", "xml:base", r);
				break;
			case "xmlLang":
				Mt(e, "http://www.w3.org/XML/1998/namespace", "xml:lang", r);
				break;
			case "xmlSpace":
				Mt(e, "http://www.w3.org/XML/1998/namespace", "xml:space", r);
				break;
			case "is":
				At(e, "is", r);
				break;
			case "innerText":
			case "textContent": break;
			default: (!(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (n = Qt.get(n) || n, At(e, n, r));
		}
	}
	function Nd(e, t, n, r, a, o) {
		switch (n) {
			case "style":
				Xt(e, r, o);
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
				typeof r == "string" ? qt(e, r) : (typeof r == "number" || typeof r == "bigint") && qt(e, "" + r);
				break;
			case "onScroll":
				r != null && $("scroll", e);
				break;
			case "onScrollEnd":
				r != null && $("scrollend", e);
				break;
			case "onClick":
				r != null && (e.onclick = tn);
				break;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "innerHTML":
			case "ref": break;
			case "innerText":
			case "textContent": break;
			default: if (!Ct.hasOwnProperty(n)) a: {
				if (n[0] === "o" && n[1] === "n" && (a = n.endsWith("Capture"), t = n.slice(2, a ? n.length - 7 : void 0), o = e[lt] || null, o = o == null ? null : o[n], typeof o == "function" && e.removeEventListener(t, o, a), typeof r == "function")) {
					typeof o != "function" && o !== null && (n in e ? e[n] = null : e.hasAttribute(n) && e.removeAttribute(n)), e.addEventListener(t, r, a);
					break a;
				}
				n in e ? e[n] = r : !0 === r ? e.setAttribute(n, "") : At(e, n, r);
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
				Ht(e, o, c, l, u, s, a, !1);
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
				t = o, n = s, e.multiple = !!r, t == null ? n != null && Wt(e, !!r, n, !0) : Wt(e, !!r, t, !1);
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
				Kt(e, r, a, o);
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
			default: if (Zt(t)) {
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
				Vt(e, s, c, l, u, d, o, a);
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
				t = c, n = s, r = m, p == null ? !!r != !!n && (t == null ? Wt(e, !!n, n ? [] : "", !1) : Wt(e, !!n, t, !0)) : Wt(e, !!n, p, !1);
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
				Gt(e, p, m);
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
			default: if (Zt(t)) {
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
						a[ht] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && a.rel.toLowerCase() === "stylesheet" || n.removeChild(a), a = o;
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
					ef(n), gt(n);
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
			} else if (!e[ht]) switch (t) {
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
		gt(e);
	}
	var mf = /* @__PURE__ */ new Map(), hf = /* @__PURE__ */ new Set();
	function gf(e) {
		return typeof e.getRootNode == "function" ? e.getRootNode() : e.nodeType === 9 ? e : e.ownerDocument;
	}
	var _f = F.d;
	F.d = {
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
		var e = _f.f(), t = vu();
		return e || t;
	}
	function yf(e) {
		var t = vt(e);
		t !== null && t.tag === 5 && t.type === "form" ? ys(t) : _f.r(e);
	}
	var bf = typeof document > "u" ? null : document;
	function xf(e, t, n) {
		var r = bf;
		if (r && typeof t == "string" && t) {
			var i = Bt(t);
			i = "link[rel=\"" + e + "\"][href=\"" + i + "\"]", typeof n == "string" && (i += "[crossorigin=\"" + n + "\"]"), hf.has(i) || (hf.add(i), e = {
				rel: e,
				crossOrigin: n,
				href: t
			}, r.querySelector(i) === null && (t = r.createElement("link"), Pd(t, "link", e), xt(t), r.head.appendChild(t)));
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
			var i = "link[rel=\"preload\"][as=\"" + Bt(t) + "\"]";
			t === "image" && n && n.imageSrcSet ? (i += "[imagesrcset=\"" + Bt(n.imageSrcSet) + "\"]", typeof n.imageSizes == "string" && (i += "[imagesizes=\"" + Bt(n.imageSizes) + "\"]")) : i += "[href=\"" + Bt(e) + "\"]";
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
			}, n), mf.set(a, e), r.querySelector(i) !== null || t === "style" && r.querySelector(jf(a)) || t === "script" && r.querySelector(Ff(a)) || (t = r.createElement("link"), Pd(t, "link", e), xt(t), r.head.appendChild(t)));
		}
	}
	function Tf(e, t) {
		_f.m(e, t);
		var n = bf;
		if (n && e) {
			var r = t && typeof t.as == "string" ? t.as : "script", i = "link[rel=\"modulepreload\"][as=\"" + Bt(r) + "\"][href=\"" + Bt(e) + "\"]", a = i;
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
				r = n.createElement("link"), Pd(r, "link", e), xt(r), n.head.appendChild(r);
			}
		}
	}
	function Ef(e, t, n) {
		_f.S(e, t, n);
		var r = bf;
		if (r && e) {
			var i = bt(r).hoistableStyles, a = Af(e);
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
					xt(c), Pd(c, "link", e), c._p = new Promise(function(e, t) {
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
			var r = bt(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), xt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
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
			var r = bt(n).hoistableScripts, i = Pf(e), a = r.get(i);
			a || (a = n.querySelector(Ff(i)), a || (e = h({
				src: e,
				async: !0,
				type: "module"
			}, t), (t = mf.get(i)) && zf(e, t), a = n.createElement("script"), xt(a), Pd(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function kf(e, t, n, r) {
		var a = (a = le.current) ? gf(a) : null;
		if (!a) throw Error(i(446));
		switch (e) {
			case "meta":
			case "title": return null;
			case "style": return typeof n.precedence == "string" && typeof n.href == "string" ? (t = Af(n.href), n = bt(a).hoistableStyles, r = n.get(t), r || (r = {
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
					var o = bt(a).hoistableStyles, s = o.get(e);
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
			case "script": return t = n.async, n = n.src, typeof n == "string" && t && typeof t != "function" && typeof t != "symbol" ? (t = Pf(n), n = bt(a).hoistableScripts, r = n.get(t), r || (r = {
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
		return "href=\"" + Bt(e) + "\"";
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
		}), Pd(t, "link", n), xt(t), e.head.appendChild(t));
	}
	function Pf(e) {
		return "[src=\"" + Bt(e) + "\"]";
	}
	function Ff(e) {
		return "script[async]" + e;
	}
	function If(e, t, n) {
		if (t.count++, t.instance === null) switch (t.type) {
			case "style":
				var r = e.querySelector("style[data-href~=\"" + Bt(n.href) + "\"]");
				if (r) return t.instance = r, xt(r), r;
				var a = h({}, n, {
					"data-href": n.href,
					"data-precedence": n.precedence,
					href: null,
					precedence: null
				});
				return r = (e.ownerDocument || e).createElement("style"), xt(r), Pd(r, "style", a), Lf(r, n.precedence, e), t.instance = r;
			case "stylesheet":
				a = Af(n.href);
				var o = e.querySelector(jf(a));
				if (o) return t.state.loading |= 4, t.instance = o, xt(o), o;
				r = Mf(n), (a = mf.get(a)) && Rf(r, a), o = (e.ownerDocument || e).createElement("link"), xt(o);
				var s = o;
				return s._p = new Promise(function(e, t) {
					s.onload = e, s.onerror = t;
				}), Pd(o, "link", r), t.state.loading |= 4, Lf(o, n.precedence, e), t.instance = o;
			case "script": return o = Pf(n.src), (a = e.querySelector(Ff(o))) ? (t.instance = a, xt(a), a) : (r = n, (a = mf.get(o)) && (r = h({}, n), zf(r, a)), e = e.ownerDocument || e, a = e.createElement("script"), xt(a), Pd(a, "link", r), e.head.appendChild(a), t.instance = a);
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
			if (!(a[ht] || a[ct] || e === "link" && a.getAttribute("rel") === "stylesheet") && a.namespaceURI !== "http://www.w3.org/2000/svg") {
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
					t = a._p, typeof t == "object" && t && typeof t.then == "function" && (e.count++, e = Jf.bind(e), t.then(e, e)), n.state.loading |= 4, n.instance = a, xt(a);
					return;
				}
				a = t.ownerDocument || t, r = Mf(r), (i = mf.get(i)) && Rf(r, i), a = a.createElement("link"), xt(a);
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
		_currentValue: ne,
		_currentValue2: ne,
		_threadCount: 0
	};
	function $f(e, t, n, r, i, a, o, s, c) {
		this.tag = 1, this.containerInfo = e, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = Ze(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Ze(0), this.hiddenUpdates = Ze(null), this.identifierPrefix = r, this.onUncaughtError = i, this.onCaughtError = a, this.onRecoverableError = o, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = c, this.incompleteTransitions = /* @__PURE__ */ new Map();
	}
	function ep(e, t, n, r, i, a, o, s, c, l, u, d) {
		return e = new $f(e, t, n, o, c, l, u, d, s), t = 1, !0 === a && (t |= 24), a = si(3, null, null, t), e.current = a, a.stateNode = e, t = sa(), t.refCount++, e.pooledCache = t, t.refCount++, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: t
		}, Ba(a), e;
	}
	function tp(e) {
		return e ? (e = ai, e) : ai;
	}
	function np(e, t, n, r, i, a) {
		i = tp(i), r.context === null ? r.context = i : r.pendingContext = i, r = Ha(t), r.payload = { element: n }, a = a === void 0 ? null : a, a !== null && (r.callback = a), n = Ua(e, r, t), n !== null && (pu(n, e, t), Wa(n, e, t));
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
			var t = ni(e, 67108864);
			t !== null && pu(t, e, 67108864), ip(e, 67108864);
		}
	}
	function op(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = du();
			t = rt(t);
			var n = ni(e, t);
			n !== null && pu(n, e, t), ip(e, t);
		}
	}
	var sp = !0;
	function cp(e, t, n, r) {
		var i = P.T;
		P.T = null;
		var a = F.p;
		try {
			F.p = 2, up(e, t, n, r);
		} finally {
			F.p = a, P.T = i;
		}
	}
	function lp(e, t, n, r) {
		var i = P.T;
		P.T = null;
		var a = F.p;
		try {
			F.p = 8, up(e, t, n, r);
		} finally {
			F.p = a, P.T = i;
		}
	}
	function up(e, t, n, r) {
		if (sp) {
			var i = dp(r);
			if (i === null) Cd(e, t, r, fp, n), Cp(e, r);
			else if (Tp(i, e, t, n, r)) r.stopPropagation();
			else if (Cp(e, r), t & 4 && -1 < Sp.indexOf(e)) {
				for (; i !== null;) {
					var a = vt(i);
					if (a !== null) switch (a.tag) {
						case 3:
							if (a = a.stateNode, a.current.memoizedState.isDehydrated) {
								var o = Ke(a.pendingLanes);
								if (o !== 0) {
									var s = a;
									for (s.pendingLanes |= 2, s.entangledLanes |= 2; o;) {
										var c = 1 << 31 - ze(o);
										s.entanglements[1] |= c, o &= ~c;
									}
									nd(a), !(Pl & 6) && ($l = De() + 500, rd(0, !1));
								}
							}
							break;
						case 31:
						case 13: s = ni(a, 2), s !== null && pu(s, a, 2), vu(), ip(a, 2);
					}
					if (a = dp(r), a === null && Cd(e, t, r, fp, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else Cd(e, t, r, null, n);
		}
	}
	function dp(e) {
		return e = rn(e), pp(e);
	}
	var fp = null;
	function pp(e) {
		if (fp = null, e = _t(e), e !== null) {
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
			case "message": switch (Oe()) {
				case ke: return 2;
				case Ae: return 8;
				case je:
				case Me: return 32;
				case Ne: return 268435456;
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
		}, t !== null && (t = vt(t), t !== null && ap(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
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
		var t = _t(e.target);
		if (t !== null) {
			var n = o(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = s(n), t !== null) {
						e.blockedOn = t, ot(e.priority, function() {
							op(n);
						});
						return;
					}
				} else if (t === 31) {
					if (t = c(n), t !== null) {
						e.blockedOn = t, ot(e.priority, function() {
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
				nn = r, n.target.dispatchEvent(r), nn = null;
			} else return t = vt(n), t !== null && ap(t), e.blockedOn = n, !1;
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
				var a = vt(n);
				a !== null && (e.splice(t, 3), t -= 3, _s(a, {
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
			var i = n[r], a = n[r + 1], o = i[lt] || null;
			if (typeof a == "function") o || Mp(n);
			else if (o) {
				var s = null;
				if (a && a.hasAttribute("formAction")) {
					if (i = a, o = a[lt] || null) s = o.formAction;
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
		np(n, du(), e, t, null, null);
	}, Ip.prototype.unmount = Fp.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			np(e.current, 2, null, e, null, null), vu(), t[ut] = null;
		}
	};
	function Ip(e) {
		this._internalRoot = e;
	}
	Ip.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = at();
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
	F.findDOMNode = function(e) {
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(i(188)) : (e = Object.keys(e).join(","), Error(i(268, e)));
		return e = d(t), e = e === null ? null : p(e), e = e === null ? null : e.stateNode, e;
	};
	var Rp = {
		bundleType: 0,
		version: "19.2.8",
		rendererPackageName: "react-dom",
		currentDispatcherRef: P,
		reconcilerVersion: "19.2.8"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var zp = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!zp.isDisabled && zp.supportsFiber) try {
			Ie = zp.inject(Rp), Le = zp;
		} catch {}
	}
	e.createRoot = function(e, t) {
		if (!a(e)) throw Error(i(299));
		var n = !1, r = "", o = Bs, s = Vs, c = Hs;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (r = t.identifierPrefix), t.onUncaughtError !== void 0 && (o = t.onUncaughtError), t.onCaughtError !== void 0 && (s = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError)), t = ep(e, 1, !1, null, null, n, r, null, o, s, c, Pp), e[ut] = t.current, xd(e), new Fp(t);
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
	for (let t of e.shipments ?? []) Array.isArray(t.attachments) || (t.attachments = []);
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
var E = /* @__PURE__ */ new Set(/* @__PURE__ */ "shipment_update.navigate.shipment_field_save.shipment_customer_save.shipment_transport_save.delivery_confirm.finance_actual_save.payment_record.payment_correction.partner_payable_record.partner_payment_record.shipment_create.pxk_generate.gnt_generate.getfly_preview.getfly_import.customer_create.customer_edit.customer_archive.customer_import.customer_getfly_import.quote_create.quote_edit.quote_transition.agreement_create.agreement_edit.agreement_transition.contract_create.contract_save.contract_goods_save.contract_docgen_generate.contract_docgen_issue.contract_shipment_link.tariff_lookup.translate_text.partner_context_select.authority_agent_save.reconciliation_filter.user_create.user_role_set.user_active_set.user_password_reset.shipment_attachment_upload.attachment_download".split(".")), D = null, O = 0;
function k(e) {
	D = e;
}
function A(e, t) {
	return !D || !E.has(e) ? !1 : (O += 1, D(e, {
		seq: O,
		event: e,
		payload: t
	}), !0);
}
//#endregion
//#region node_modules/react-router/dist/development/chunk-BV7QT456.mjs
var ee = /^(?:[a-z][a-z0-9+.-]*:|[\\/]{2})/i, j = /^[\\/]{2}/;
function M(e, t) {
	return t + e.replace(/\\/g, "/");
}
function N(e) {
	return typeof e == "object" && !!e && "pathname" in e && "search" in e && "hash" in e && "state" in e && "key" in e;
}
function te(e = {}) {
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
		let a = re(i ? l().pathname : "/", e, t, n, r);
		return F(a.pathname.charAt(0) === "/", `relative pathnames are not supported in memory history: ${JSON.stringify(e)}`), a;
	}
	function d(e) {
		return typeof e == "string" ? e : ie(e);
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
			let t = typeof e == "string" ? ae(e) : e;
			return {
				pathname: t.pathname || "",
				search: t.search || "",
				hash: t.hash || ""
			};
		},
		push(e, t) {
			o = "PUSH";
			let n = N(e) ? e : u(e, t);
			a += 1, i.splice(a, i.length, n), r && s && s({
				action: o,
				location: n,
				delta: 1
			});
		},
		replace(e, t) {
			o = "REPLACE";
			let n = N(e) ? e : u(e, t);
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
function P(e, t) {
	if (e === !1 || e == null) throw Error(t);
}
function F(e, t) {
	if (!e) {
		typeof console < "u" && console.warn(t);
		try {
			throw Error(t);
		} catch {}
	}
}
function ne() {
	return Math.random().toString(36).substring(2, 10);
}
function re(e, t, n = null, r, i) {
	return {
		pathname: typeof e == "string" ? e : e.pathname,
		search: "",
		hash: "",
		...typeof t == "string" ? ae(t) : t,
		state: n,
		key: t && t.key || r || ne(),
		mask: i
	};
}
function ie({ pathname: e = "/", search: t = "", hash: n = "" }) {
	return t && t !== "?" && (e += t.charAt(0) === "?" ? t : "?" + t), n && n !== "#" && (e += n.charAt(0) === "#" ? n : "#" + n), e;
}
function ae(e) {
	let t = {};
	if (e) {
		let n = e.indexOf("#");
		n >= 0 && (t.hash = e.substring(n), e = e.substring(0, n));
		let r = e.indexOf("?");
		r >= 0 && (t.search = e.substring(r), e = e.substring(0, r)), e && (t.pathname = e);
	}
	return t;
}
function oe(e, t, n = "/") {
	return I(e, t, n, !1);
}
function I(e, t, n, r, i) {
	let a = Te((typeof t == "string" ? ae(t) : t).pathname || "/", n);
	if (a == null) return null;
	let o = i ?? se(e), s = null, c = we(a);
	for (let e = 0; s == null && e < o.length; ++e) s = be(o[e], c, r);
	return s;
}
function se(e) {
	let t = ce(e);
	return ue(t), t;
}
function ce(e, t = [], n = [], r = "", i = !1) {
	let a = (e, a, o = i, s) => {
		let c = {
			relativePath: s === void 0 ? e.path || "" : s,
			caseSensitive: e.caseSensitive === !0,
			childrenIndex: a,
			route: e
		};
		if (c.relativePath.startsWith("/")) {
			if (!c.relativePath.startsWith(r) && o) return;
			P(c.relativePath.startsWith(r), `Absolute route path "${c.relativePath}" nested under path "${r}" is not valid. An absolute child route path must start with the combined path of all its parent routes.`), c.relativePath = c.relativePath.slice(r.length);
		}
		let l = Ne([r, c.relativePath]), u = n.concat(c);
		e.children && e.children.length > 0 && (P(e.index !== !0, `Index routes must not have child routes. Please remove all child routes from route path "${l}".`), ce(e.children, t, u, l, o)), (e.path != null || e.index) && t.push({
			path: l,
			score: ve(l, e.index),
			routesMeta: u.map((e, t) => {
				let [n, r] = Ce(e.relativePath, e.caseSensitive, t === u.length - 1);
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
		else for (let n of le(e.path)) a(e, t, !0, n);
	}), t;
}
function le(e) {
	let t = e.split("/");
	if (t.length === 0) return [];
	let [n, ...r] = t, i = n.endsWith("?"), a = n.replace(/\?$/, "");
	if (r.length === 0) return i ? [a, ""] : [a];
	let o = le(r.join("/")), s = [];
	return s.push(...o.map((e) => e === "" ? a : [a, e].join("/"))), i && s.push(...o), s.map((t) => e.startsWith("/") && t === "" ? "/" : t);
}
function ue(e) {
	e.sort((e, t) => e.score === t.score ? ye(e.routesMeta.map((e) => e.childrenIndex), t.routesMeta.map((e) => e.childrenIndex)) : t.score - e.score);
}
var de = /^:[\w-]+$/, fe = 3, pe = 2, me = 1, he = 10, ge = -2, _e = (e) => e === "*";
function ve(e, t) {
	let n = e.split("/"), r = n.length;
	return n.some(_e) && (r += ge), t && (r += pe), n.filter((e) => !_e(e)).reduce((e, t) => e + (de.test(t) ? fe : t === "" ? me : he), r);
}
function ye(e, t) {
	return e.length === t.length && e.slice(0, -1).every((e, n) => e === t[n]) ? e[e.length - 1] - t[t.length - 1] : 0;
}
function be(e, t, n = !1) {
	let { routesMeta: r } = e, i = {}, a = "/", o = [];
	for (let e = 0; e < r.length; ++e) {
		let s = r[e], c = e === r.length - 1, l = a === "/" ? t : t.slice(a.length) || "/", u = {
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: c
		}, d = s.matcher && s.compiledParams ? Se(u, l, s.matcher, s.compiledParams) : xe(u, l), f = s.route;
		if (!d && c && n && !r[r.length - 1].route.index && (d = xe({
			path: s.relativePath,
			caseSensitive: s.caseSensitive,
			end: !1
		}, l)), !d) return null;
		Object.assign(i, d.params), o.push({
			params: i,
			pathname: Ne([a, d.pathname]),
			pathnameBase: Fe(Ne([a, d.pathnameBase])),
			route: f
		}), d.pathnameBase !== "/" && (a = Ne([a, d.pathnameBase]));
	}
	return o;
}
function xe(e, t) {
	typeof e == "string" && (e = {
		path: e,
		caseSensitive: !1,
		end: !0
	});
	let [n, r] = Ce(e.path, e.caseSensitive, e.end);
	return Se(e, t, n, r);
}
function Se(e, t, n, r) {
	let i = t.match(n);
	if (!i) return null;
	let a = i[0], o = Pe(a, 1), s = i.slice(1);
	return {
		params: r.reduce((e, { paramName: t, isOptional: n }, r) => {
			if (t === "*") {
				let e = s[r] || "";
				o = Pe(a.slice(0, a.length - e.length), 1);
			}
			let i = s[r];
			return e[t] = n && !i ? void 0 : (i || "").replace(/%2F/g, "/"), e;
		}, {}),
		pathname: a,
		pathnameBase: o,
		pattern: e
	};
}
function Ce(e, t = !1, n = !0) {
	F(e === "*" || !e.endsWith("*") || e.endsWith("/*"), `Route path "${e}" will be treated as if it were "${e.replace(/\*$/, "/*")}" because the \`*\` character must always follow a \`/\` in the pattern. To get rid of this warning, please change the route path to "${e.replace(/\*$/, "/*")}".`);
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
function we(e) {
	try {
		return e.split("/").map((e) => decodeURIComponent(e).replace(/\//g, "%2F")).join("/");
	} catch (t) {
		return F(!1, `The URL path "${e}" could not be decoded because it is a malformed URL segment. This is probably due to a bad percent encoding (${t}).`), e;
	}
}
function Te(e, t) {
	if (t === "/") return e;
	if (!e.toLowerCase().startsWith(t.toLowerCase())) return null;
	let n = t.endsWith("/") ? t.length - 1 : t.length, r = e.charAt(n);
	return r && r !== "/" ? null : e.slice(n) || "/";
}
function Ee(e, t = "/") {
	let { pathname: n, search: r = "", hash: i = "" } = typeof e == "string" ? ae(e) : e, a;
	return n ? (n = Me(n), a = n.startsWith("/") || n.startsWith("\\") ? De(n.substring(1), "/") : De(n, t)) : a = t, {
		pathname: a,
		search: Ie(r),
		hash: Le(i)
	};
}
function De(e, t) {
	let n = Pe(t).split("/");
	return e.split("/").forEach((e) => {
		e === ".." ? n.length > 1 && n.pop() : e !== "." && n.push(e);
	}), n.length > 1 ? n.join("/") : "/";
}
function Oe(e, t, n, r) {
	return `Cannot include a '${e}' character in a manually specified \`to.${t}\` field [${JSON.stringify(r)}].  Please separate it out to the \`to.${n}\` field. Alternatively you may provide the full path as a string in <Link to="..."> and the router will parse it for you.`;
}
function ke(e) {
	return e.filter((e, t) => t === 0 || e.route.path && e.route.path.length > 0);
}
function Ae(e) {
	let t = ke(e);
	return t.map((e, n) => n === t.length - 1 ? e.pathname : e.pathnameBase);
}
function je(e, t, n, r = !1) {
	let i;
	typeof e == "string" ? i = ae(e) : (i = { ...e }, P(!i.pathname || !i.pathname.includes("?"), Oe("?", "pathname", "search", i)), P(!i.pathname || !i.pathname.includes("#"), Oe("#", "pathname", "hash", i)), P(!i.search || !i.search.includes("#"), Oe("#", "search", "hash", i)));
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
	let c = Ee(i, s), l = o && o !== "/" && o.endsWith("/"), u = (a || o === ".") && n.endsWith("/");
	return !c.pathname.endsWith("/") && (l || u) && (c.pathname += "/"), c;
}
var Me = (e) => e.replace(/[\\/]{2,}/g, "/"), Ne = (e) => Me(e.join("/"));
function Pe(e, t = 0) {
	let n = e.length;
	for (; n > t && e.charCodeAt(n - 1) === 47;) n--;
	return n === e.length ? e : e.slice(0, n);
}
var Fe = (e) => Pe(e).replace(/^\/*/, "/"), Ie = (e) => !e || e === "?" ? "" : e.startsWith("?") ? e : "?" + e, Le = (e) => !e || e === "#" ? "" : e.startsWith("#") ? e : "#" + e, Re = class {
	constructor(e, t, n, r = !1) {
		this.status = e, this.statusText = t || "", this.internal = r, n instanceof Error ? (this.data = n.toString(), this.error = n) : this.data = n;
	}
};
function ze(e) {
	return e != null && typeof e.status == "number" && typeof e.statusText == "string" && typeof e.internal == "boolean" && "data" in e;
}
function Be(e) {
	return Ne(e.map((e) => e.route.path).filter(Boolean)) || "/";
}
var Ve = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
function He(e, t) {
	let n = e;
	if (typeof n != "string" || !ee.test(n)) return {
		absoluteURL: void 0,
		isExternal: !1,
		to: n
	};
	let r = n, i = !1;
	if (Ve) try {
		let e = new URL(window.location.href), r = j.test(n) ? new URL(M(n, e.protocol)) : new URL(n), a = Te(r.pathname, t);
		r.origin === e.origin && a != null ? n = a + r.search + r.hash : i = !0;
	} catch {
		F(!1, `<Link to="${n}"> contains an invalid URL which will probably break when clicked - please update to a valid URL path.`);
	}
	return {
		absoluteURL: r,
		isExternal: i,
		to: n
	};
}
Object.getOwnPropertyNames(Object.prototype).sort().join("\0");
var Ue = new URL("http://localhost");
function We(e) {
	if (e.createURL) return e.createURL("/");
	try {
		return new URL(e.createHref("/"), Ue);
	} catch {
		return Ue;
	}
}
function Ge(e, t) {
	return e.origin === t.origin && (e.origin !== "null" || e.protocol === t.protocol && e.host === t.host);
}
function Ke(e, t) {
	if (e.startsWith("//")) return !0;
	let n = t.protocol.toLowerCase();
	return e.toLowerCase().startsWith(n) ? t.host === "" || e.slice(n.length).startsWith("//") : !1;
}
function qe(e, t, n, r) {
	let i = null;
	try {
		i = e == null ? null : new URL(e, n);
	} catch {}
	let a = new URL(t, n), o = i != null && !Ge(i, n), s = !Ge(a, n);
	if (r === "reject") {
		if (o || s) throw Error("External navigation is not allowed");
	} else if (s && (i == null || !Ke(e, i) || !Ge(i, a))) throw Error("External navigation is not allowed");
}
var Je = [
	"POST",
	"PUT",
	"PATCH",
	"DELETE"
];
new Set(Je);
var Ye = ["GET", ...Je];
new Set(Ye);
var Xe = [
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
function Ze(e) {
	try {
		return Xe.includes(new URL(e).protocol);
	} catch {
		return !1;
	}
}
var Qe = _.createContext(null);
Qe.displayName = "DataRouter";
var $e = _.createContext(null);
$e.displayName = "DataRouterState";
var et = _.createContext(!1);
function tt() {
	return _.useContext(et);
}
var nt = _.createContext({ isTransitioning: !1 });
nt.displayName = "ViewTransition";
var rt = _.createContext(/* @__PURE__ */ new Map());
rt.displayName = "Fetchers";
var it = _.createContext(null);
it.displayName = "Await";
var at = _.createContext(null);
at.displayName = "Navigation";
var ot = _.createContext(null);
ot.displayName = "Location";
var st = _.createContext({
	outlet: null,
	matches: [],
	isDataRoute: !1
});
st.displayName = "Route";
var ct = _.createContext(null);
ct.displayName = "RouteError";
var lt = "REACT_ROUTER_ERROR", ut = "REDIRECT", dt = "ROUTE_ERROR_RESPONSE";
function ft(e) {
	if (e.startsWith(`${lt}:${ut}:{`)) try {
		let t = JSON.parse(e.slice(28));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string" && typeof t.location == "string" && typeof t.reloadDocument == "boolean" && typeof t.replace == "boolean") return t;
	} catch {}
}
function pt(e) {
	if (e.startsWith(`${lt}:${dt}:{`)) try {
		let t = JSON.parse(e.slice(40));
		if (typeof t == "object" && t && typeof t.status == "number" && typeof t.statusText == "string") return new Re(t.status, t.statusText, t.data);
	} catch {}
}
function mt(e, { relative: t } = {}) {
	P(ht(), "useHref() may be used only in the context of a <Router> component.");
	let { basename: n, navigator: r } = _.useContext(at), { hash: i, pathname: a, search: o } = St(e, { relative: t }), s = a;
	return n !== "/" && (s = a === "/" ? n : Ne([n, a])), r.createHref({
		pathname: s,
		search: o,
		hash: i
	});
}
function ht() {
	return _.useContext(ot) != null;
}
function gt() {
	return P(ht(), "useLocation() may be used only in the context of a <Router> component."), _.useContext(ot).location;
}
var _t = "You should call navigate() in a React.useEffect(), not when your component is first rendered.";
function vt(e) {
	_.useContext(at).static || _.useLayoutEffect(e);
}
function yt() {
	let { isDataRoute: e } = _.useContext(st);
	return e ? zt() : bt();
}
function bt() {
	P(ht(), "useNavigate() may be used only in the context of a <Router> component.");
	let e = _.useContext(Qe), { basename: t, navigator: n } = _.useContext(at), { matches: r } = _.useContext(st), { pathname: i } = gt(), a = JSON.stringify(Ae(r)), o = _.useRef(!1);
	return vt(() => {
		o.current = !0;
	}), _.useCallback((r, s = {}) => {
		if (F(o.current, _t), !o.current) return;
		if (typeof r == "number") {
			n.go(r);
			return;
		}
		let c = je(r, JSON.parse(a), i, s.relative === "path");
		e == null && t !== "/" && (c.pathname = c.pathname === "/" ? t : Ne([t, c.pathname])), qe(typeof r == "string" ? r : ie(r), n.createHref(c), We(n), "reject"), (s.replace ? n.replace : n.push)(c, s.state, s);
	}, [
		t,
		n,
		a,
		i,
		e
	]);
}
_.createContext(null);
function xt() {
	let { matches: e } = _.useContext(st);
	return e[e.length - 1]?.params ?? {};
}
function St(e, { relative: t } = {}) {
	let { matches: n } = _.useContext(st), { pathname: r } = gt(), i = JSON.stringify(Ae(n));
	return _.useMemo(() => je(e, JSON.parse(i), r, t === "path"), [
		e,
		i,
		r,
		t
	]);
}
function Ct(e, t) {
	return wt(e, t);
}
function wt(e, t, n) {
	P(ht(), "useRoutes() may be used only in the context of a <Router> component.");
	let { navigator: r } = _.useContext(at), { matches: i } = _.useContext(st), a = i[i.length - 1], o = a ? a.params : {}, s = a ? a.pathname : "/", c = a ? a.pathnameBase : "/", l = a && a.route;
	{
		let e = l && l.path || "";
		Vt(s, !l || e.endsWith("*") || e.endsWith("*?"), `You rendered descendant <Routes> (or called \`useRoutes()\`) at "${s}" (under <Route path="${e}">) but the parent route path has no trailing "*". This means if you navigate deeper, the parent won't match anymore and therefore the child routes will never render.

Please change the parent <Route path="${e}"> to <Route path="${e === "/" ? "*" : `${e}/*`}">.`);
	}
	let u = gt(), d;
	if (t) {
		let e = typeof t == "string" ? ae(t) : t;
		P(c === "/" || e.pathname?.startsWith(c), `When overriding the location using \`<Routes location>\` or \`useRoutes(routes, location)\`, the location pathname must begin with the portion of the URL pathname that was matched by all parent routes. The current pathname base is "${c}" but pathname "${e.pathname}" was given in the \`location\` prop.`), d = e;
	} else d = u;
	let f = d.pathname || "/", p = f;
	if (c !== "/") {
		let e = c.replace(/^\//, "").split("/");
		p = "/" + f.replace(/^\//, "").split("/").slice(e.length).join("/");
	}
	let m = n && n.state.matches.length ? n.state.matches.map((e) => Object.assign(e, { route: n.manifest[e.route.id] || e.route })) : oe(e, { pathname: p });
	F(l || m != null, `No routes matched location "${d.pathname}${d.search}${d.hash}" `), F(m == null || m[m.length - 1].route.element !== void 0 || m[m.length - 1].route.Component !== void 0 || m[m.length - 1].route.lazy !== void 0, `Matched leaf route at location "${d.pathname}${d.search}${d.hash}" does not have an element or Component. This means it will render an <Outlet /> with a null value by default resulting in an "empty" page.`);
	let h = jt(m && m.map((e) => Object.assign({}, e, {
		params: Object.assign({}, o, e.params),
		pathname: Ne([c, r.encodeLocation ? r.encodeLocation(e.pathname.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathname]),
		pathnameBase: e.pathnameBase === "/" ? c : Ne([c, r.encodeLocation ? r.encodeLocation(e.pathnameBase.replace(/%/g, "%25").replace(/\?/g, "%3F").replace(/#/g, "%23")).pathname : e.pathnameBase])
	})), i, n);
	return t && h ? /* @__PURE__ */ _.createElement(ot.Provider, { value: {
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
function Tt() {
	let e = Rt(), t = ze(e) ? `${e.status} ${e.statusText}` : e instanceof Error ? e.message : JSON.stringify(e), n = e instanceof Error ? e.stack : null, r = "rgba(200,200,200, 0.5)", i = {
		padding: "0.5rem",
		backgroundColor: r
	}, a = {
		padding: "2px 4px",
		backgroundColor: r
	}, o = null;
	return console.error("Error handled by React Router default ErrorBoundary:", e), o = /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("p", null, "💿 Hey developer 👋"), /* @__PURE__ */ _.createElement("p", null, "You can provide a way better UX than this when your app throws errors by providing your own ", /* @__PURE__ */ _.createElement("code", { style: a }, "ErrorBoundary"), " or", " ", /* @__PURE__ */ _.createElement("code", { style: a }, "errorElement"), " prop on your route.")), /* @__PURE__ */ _.createElement(_.Fragment, null, /* @__PURE__ */ _.createElement("h2", null, "Unexpected Application Error!"), /* @__PURE__ */ _.createElement("h3", { style: { fontStyle: "italic" } }, t), n ? /* @__PURE__ */ _.createElement("pre", { style: i }, n) : null, o);
}
var Et = /* @__PURE__ */ _.createElement(Tt, null), Dt = class extends _.Component {
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
			let t = pt(e.digest);
			t && (e = t);
		}
		let t = e === void 0 ? this.props.children : /* @__PURE__ */ _.createElement(st.Provider, { value: this.props.routeContext }, /* @__PURE__ */ _.createElement(ct.Provider, {
			value: e,
			children: this.props.component
		}));
		return this.context ? /* @__PURE__ */ _.createElement(kt, { error: e }, t) : t;
	}
};
Dt.contextType = et;
var Ot = /* @__PURE__ */ new WeakMap();
function kt({ children: e, error: t }) {
	let { basename: n, navigator: r } = _.useContext(at);
	if (typeof t == "object" && t && "digest" in t && typeof t.digest == "string") {
		let e = ft(t.digest);
		if (e) {
			let i = Ot.get(t);
			if (i) throw i;
			let a = He(e.location, n), o = a.absoluteURL || a.to;
			if (qe(e.location, o, We(r), "allow-explicit"), Ze(o)) throw Error("Invalid redirect location");
			if (Ve && !Ot.get(t)) {
				if (a.isExternal || e.reloadDocument) window.location.href = o;
				else {
					let n = Promise.resolve().then(() => window.__reactRouterDataRouter.navigate(a.to, { replace: e.replace }));
					throw Ot.set(t, n), n;
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
function At({ routeContext: e, match: t, children: n }) {
	let r = _.useContext(Qe);
	return r && r.static && r.staticContext && (t.route.errorElement || t.route.ErrorBoundary) && (r.staticContext._deepestRenderedBoundaryId = t.route.id), /* @__PURE__ */ _.createElement(st.Provider, { value: e }, n);
}
function jt(e, t = [], n) {
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
		P(e >= 0, `Could not find a matching route for errors on route IDs: ${Object.keys(a).join(",")}`), i = i.slice(0, Math.min(i.length, e + 1));
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
			pattern: Be(r.matches),
			errorInfo: t
		});
	} : void 0;
	return i.reduceRight((e, n, c) => {
		let u, d = !1, f = null, p = null;
		r && (u = a && n.route.id ? a[n.route.id] : void 0, f = n.route.errorElement || Et, o && (s < 0 && c === 0 ? (Vt("route-fallback", !1, "No `HydrateFallback` element provided to render during initial hydration"), d = !0, p = null) : s === c && (d = !0, p = n.route.hydrateFallbackElement || null)));
		let m = t.concat(i.slice(0, c + 1)), h = () => {
			let t;
			return t = u ? f : d ? p : n.route.Component ? /* @__PURE__ */ _.createElement(n.route.Component, null) : n.route.element ? n.route.element : e, /* @__PURE__ */ _.createElement(At, {
				match: n,
				routeContext: {
					outlet: e,
					matches: m,
					isDataRoute: r != null
				},
				children: t
			});
		};
		return r && (n.route.ErrorBoundary || n.route.errorElement || c === 0) ? /* @__PURE__ */ _.createElement(Dt, {
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
function Mt(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function Nt(e) {
	let t = _.useContext(Qe);
	return P(t, Mt(e)), t;
}
function Pt(e) {
	let t = _.useContext($e);
	return P(t, Mt(e)), t;
}
function Ft(e) {
	let t = _.useContext(st);
	return P(t, Mt(e)), t;
}
function It(e) {
	let t = Ft(e), n = t.matches[t.matches.length - 1];
	return P(n.route.id, `${e} can only be used on routes that contain a unique "id"`), n.route.id;
}
function Lt() {
	return It("useRouteId");
}
function Rt() {
	let e = _.useContext(ct), t = Pt("useRouteError"), n = It("useRouteError");
	return e === void 0 ? t.errors?.[n] : e;
}
function zt() {
	let { router: e } = Nt("useNavigate"), t = It("useNavigate"), n = _.useRef(!1);
	return vt(() => {
		n.current = !0;
	}), _.useCallback(async (r, i = {}) => {
		F(n.current, _t), n.current && (typeof r == "number" ? await e.navigate(r) : await e.navigate(r, {
			fromRouteId: t,
			...i
		}));
	}, [e, t]);
}
var Bt = {};
function Vt(e, t, n) {
	!t && !Bt[e] && (Bt[e] = !0, F(!1, n));
}
_.memo(Ht);
function Ht({ routes: e, manifest: t, future: n, state: r, isStatic: i, onError: a }) {
	return wt(e, void 0, {
		manifest: t,
		state: r,
		isStatic: i,
		onError: a,
		future: n
	});
}
function Ut({ basename: e, children: t, initialEntries: n, initialIndex: r, useTransitions: i }) {
	let a = _.useRef();
	a.current ?? (a.current = te({
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
	return _.useLayoutEffect(() => o.listen(l), [o, l]), /* @__PURE__ */ _.createElement(Gt, {
		basename: e,
		children: t,
		location: s.location,
		navigationType: s.action,
		navigator: o,
		useTransitions: i
	});
}
function Wt(e) {
	P(!1, "A <Route> is only ever to be used as the child of <Routes> element, never rendered directly. Please wrap your <Route> in a <Routes>.");
}
function Gt({ basename: e = "/", children: t = null, location: n, navigationType: r = "POP", navigator: i, static: a = !1, useTransitions: o }) {
	P(!ht(), "You cannot render a <Router> inside another <Router>. You should never have more than one in your app.");
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
	typeof n == "string" && (n = ae(n));
	let { pathname: l = "/", search: u = "", hash: d = "", state: f = null, key: p = "default", mask: m } = n, h = _.useMemo(() => {
		let e = Te(l, s);
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
	return F(h != null, `<Router basename="${s}"> is not able to match the URL "${l}${u}${d}" because it does not start with the basename, so the <Router> won't render anything.`), h == null ? null : /* @__PURE__ */ _.createElement(at.Provider, { value: c }, /* @__PURE__ */ _.createElement(ot.Provider, {
		children: t,
		value: h
	}));
}
function Kt({ children: e, location: t }) {
	return Ct(qt(e), t);
}
_.Component;
function qt(e, t = []) {
	let n = [];
	return _.Children.forEach(e, (e, r) => {
		if (!_.isValidElement(e)) return;
		let i = [...t, r];
		if (e.type === _.Fragment) {
			n.push.apply(n, qt(e.props.children, i));
			return;
		}
		P(e.type === Wt, `[${typeof e.type == "string" ? e.type : e.type.name}] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>`), P(!e.props.index || !e.props.children, "An index route cannot have child routes.");
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
		e.props.children && (a.children = qt(e.props.children, i)), n.push(a);
	}), n;
}
var Jt = "get", Yt = "application/x-www-form-urlencoded";
function Xt(e) {
	return typeof HTMLElement < "u" && e instanceof HTMLElement;
}
function Zt(e) {
	return Xt(e) && e.tagName.toLowerCase() === "button";
}
function Qt(e) {
	return Xt(e) && e.tagName.toLowerCase() === "form";
}
function $t(e) {
	return Xt(e) && e.tagName.toLowerCase() === "input";
}
function en(e) {
	return !!(e.metaKey || e.altKey || e.ctrlKey || e.shiftKey);
}
function tn(e, t) {
	return e.button === 0 && (!t || t === "_self") && !en(e);
}
function nn(e = "") {
	return new URLSearchParams(typeof e == "string" || Array.isArray(e) || e instanceof URLSearchParams ? e : Object.keys(e).reduce((t, n) => {
		let r = e[n];
		return t.concat(Array.isArray(r) ? r.map((e) => [n, e]) : [[n, r]]);
	}, []));
}
function rn(e, t) {
	let n = nn(e);
	return t && t.forEach((e, r) => {
		n.has(r) || t.getAll(r).forEach((e) => {
			n.append(r, e);
		});
	}), n;
}
var an = null;
function on() {
	if (an === null) try {
		new FormData(document.createElement("form"), 0), an = !1;
	} catch {
		an = !0;
	}
	return an;
}
var sn = /* @__PURE__ */ new Set([
	"application/x-www-form-urlencoded",
	"multipart/form-data",
	"text/plain"
]);
function cn(e) {
	return e != null && !sn.has(e) ? (F(!1, `"${e}" is not a valid \`encType\` for \`<Form>\`/\`<fetcher.Form>\` and will default to "${Yt}"`), null) : e;
}
function ln(e, t) {
	let n, r, i, a, o;
	if (Qt(e)) {
		let o = e.getAttribute("action");
		r = o ? Te(o, t) : null, n = e.getAttribute("method") || Jt, i = cn(e.getAttribute("enctype")) || Yt, a = new FormData(e);
	} else if (Zt(e) || $t(e) && (e.type === "submit" || e.type === "image")) {
		let o = e.form;
		if (o == null) throw Error("Cannot submit a <button> or <input type=\"submit\"> without a <form>");
		let s = e.getAttribute("formaction") || o.getAttribute("action");
		if (r = s ? Te(s, t) : null, n = e.getAttribute("formmethod") || o.getAttribute("method") || Jt, i = cn(e.getAttribute("formenctype")) || cn(o.getAttribute("enctype")) || Yt, a = new FormData(o, e), !on()) {
			let { name: t, type: n, value: r } = e;
			if (n === "image") {
				let e = t ? `${t}.` : "";
				a.append(`${e}x`, "0"), a.append(`${e}y`, "0");
			} else t && a.append(t, r);
		}
	} else if (Xt(e)) throw Error("Cannot submit element that is not <form>, <button>, or <input type=\"submit|image\">");
	else n = Jt, r = null, i = Yt, o = e;
	return a && i === "text/plain" && (o = a, a = void 0), {
		action: r,
		method: n.toLowerCase(),
		encType: i,
		formData: a,
		body: o
	};
}
Object.getOwnPropertyNames(Object.prototype).sort().join("\0");
function un(e, t) {
	if (e === !1 || e == null) throw Error(t);
}
function dn(e, t, n, r) {
	let i = typeof e == "string" ? new URL(e, typeof window > "u" ? "server://singlefetch/" : window.location.origin) : e;
	return i.pathname = n ? i.pathname.endsWith("/") ? `${i.pathname}_.${r}` : `${i.pathname}.${r}` : i.pathname === "/" ? `_root.${r}` : t && Te(i.pathname, t) === "/" ? `${Pe(t)}/_root.${r}` : `${Pe(i.pathname)}.${r}`, i;
}
async function fn(e, t) {
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
function pn(e) {
	return e != null && typeof e.page == "string";
}
function mn(e) {
	return e == null ? !1 : e.href == null ? e.rel === "preload" && typeof e.imageSrcSet == "string" && typeof e.imageSizes == "string" : typeof e.rel == "string" && typeof e.href == "string";
}
async function hn(e, t, n) {
	return bn((await Promise.all(e.map(async (e) => {
		let r = t.routes[e.route.id];
		if (r) {
			let e = await fn(r, n);
			return e.links ? e.links() : [];
		}
		return [];
	}))).flat(1).filter(mn).filter((e) => e.rel === "stylesheet" || e.rel === "preload").map((e) => e.rel === "stylesheet" ? {
		...e,
		rel: "prefetch",
		as: "style"
	} : {
		...e,
		rel: "prefetch"
	}));
}
function gn(e, t, n, r, i, a) {
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
function _n(e, t, { includeHydrateFallback: n } = {}) {
	return vn(e.map((e) => {
		let r = t.routes[e.route.id];
		if (!r) return [];
		let i = [r.module];
		return r.clientActionModule && (i = i.concat(r.clientActionModule)), r.clientLoaderModule && (i = i.concat(r.clientLoaderModule)), n && r.hydrateFallbackModule && (i = i.concat(r.hydrateFallbackModule)), r.imports && (i = i.concat(r.imports)), i;
	}).flat(1));
}
function vn(e) {
	return [...new Set(e)];
}
function yn(e) {
	let t = {}, n = Object.keys(e).sort();
	for (let r of n) t[r] = e[r];
	return t;
}
function bn(e, t) {
	let n = /* @__PURE__ */ new Set(), r = new Set(t);
	return e.reduce((e, i) => {
		if (t && !pn(i) && i.as === "script" && i.href && r.has(i.href)) return e;
		let a = JSON.stringify(yn(i));
		return n.has(a) || (n.add(a), e.push({
			key: a,
			link: i
		})), e;
	}, []);
}
function xn() {
	let e = _.useContext(Qe);
	return un(e, "You must render this element inside a <DataRouterContext.Provider> element"), e;
}
function Sn() {
	let e = _.useContext($e);
	return un(e, "You must render this element inside a <DataRouterStateContext.Provider> element"), e;
}
var Cn = _.createContext(void 0);
Cn.displayName = "FrameworkContext";
function wn() {
	let e = _.useContext(Cn);
	return un(e, "You must render this element inside a <HydratedRouter> element"), e;
}
function Tn(e, t) {
	let n = _.useContext(Cn), [r, i] = _.useState(!1), [a, o] = _.useState(!1), { onFocus: s, onBlur: c, onMouseEnter: l, onMouseLeave: u, onTouchStart: d } = t, f = _.useRef(null);
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
			onFocus: En(s, p),
			onBlur: En(c, m),
			onMouseEnter: En(l, p),
			onMouseLeave: En(u, m),
			onTouchStart: En(d, p)
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
function En(e, t) {
	return (n) => {
		e && e(n), n.defaultPrevented || t(n);
	};
}
function Dn({ page: e, ...t }) {
	let n = tt(), { nonce: r } = wn(), { router: i } = xn(), a = _.useMemo(() => oe(i.routes, e, i.basename), [
		i.routes,
		e,
		i.basename
	]);
	return a ? (t.nonce == null && r && (t = {
		...t,
		nonce: r
	}), n ? /* @__PURE__ */ _.createElement(kn, {
		page: e,
		matches: a,
		...t
	}) : /* @__PURE__ */ _.createElement(An, {
		page: e,
		matches: a,
		...t
	})) : null;
}
function On(e) {
	let { manifest: t, routeModules: n } = wn(), [r, i] = _.useState([]);
	return _.useEffect(() => {
		let r = !1;
		return hn(e, t, n).then((e) => {
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
function kn({ page: e, matches: t, ...n }) {
	let r = gt(), { future: i } = wn(), { basename: a } = xn(), o = _.useMemo(() => {
		if (e === r.pathname + r.search + r.hash) return [];
		let n = dn(e, a, i.v8_trailingSlashAwareDataRequests, "rsc"), o = !1, s = [];
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
function An({ page: e, matches: t, ...n }) {
	let r = gt(), { future: i, manifest: a, routeModules: o } = wn(), { basename: s } = xn(), { loaderData: c, matches: l } = Sn(), u = _.useMemo(() => gn(e, t, l, a, r, "data"), [
		e,
		t,
		l,
		a,
		r
	]), d = _.useMemo(() => gn(e, t, l, a, r, "assets"), [
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
		let d = dn(e, s, i.v8_trailingSlashAwareDataRequests, "data");
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
	]), p = _.useMemo(() => _n(d, a), [d, a]), m = On(d);
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
function jn(...e) {
	return (t) => {
		e.forEach((e) => {
			typeof e == "function" ? e(t) : e != null && (e.current = t);
		});
	};
}
_.Component;
var Mn = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0;
try {
	Mn && (window.__reactRouterVersion = "7.18.3");
} catch {}
var L = _.forwardRef(function({ onClick: e, discover: t = "render", prefetch: n = "none", relative: r, reloadDocument: i, replace: a, mask: o, state: s, target: c, to: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) {
	let { basename: h, navigator: g, useTransitions: v } = _.useContext(at), y = typeof l == "string" && ee.test(l), b = He(l, h);
	l = b.to;
	let x = mt(l, { relative: r }), S = gt(), C = null;
	if (o) {
		let e = je(o, [], S.mask ? S.mask.pathname : "/", !0);
		h !== "/" && (e.pathname = e.pathname === "/" ? h : Ne([h, e.pathname])), C = g.createHref(e);
	}
	let [w, T, E] = Tn(n, p), D = Ln(l, {
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
	let k = !(b.isExternal || i), A = /* @__PURE__ */ _.createElement("a", {
		...p,
		...E,
		href: (k ? C : void 0) || b.absoluteURL || x,
		onClick: k ? O : e,
		ref: jn(m, T),
		target: c,
		"data-discover": !y && t === "render" ? "true" : void 0
	});
	return w && !y ? /* @__PURE__ */ _.createElement(_.Fragment, null, A, /* @__PURE__ */ _.createElement(Dn, { page: x })) : A;
});
L.displayName = "Link";
var Nn = _.forwardRef(function({ "aria-current": e = "page", caseSensitive: t = !1, className: n = "", end: r = !1, style: i, to: a, viewTransition: o, children: s, ...c }, l) {
	let u = St(a, { relative: c.relative }), d = gt(), f = _.useContext($e), { navigator: p, basename: m } = _.useContext(at), h = f != null && Un(u) && o === !0, g = p.encodeLocation ? p.encodeLocation(u).pathname : u.pathname, v = d.pathname, y = f && f.navigation && f.navigation.location ? f.navigation.location.pathname : null;
	t || (v = v.toLowerCase(), y = y ? y.toLowerCase() : null, g = g.toLowerCase()), y && m && (y = Te(y, m) || y);
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
	return /* @__PURE__ */ _.createElement(L, {
		...c,
		"aria-current": w,
		className: T,
		ref: l,
		style: E,
		to: a,
		viewTransition: o
	}, typeof s == "function" ? s(C) : s);
});
Nn.displayName = "NavLink";
var Pn = _.forwardRef(({ discover: e = "render", fetcherKey: t, navigate: n, reloadDocument: r, replace: i, state: a, method: o = Jt, action: s, onSubmit: c, relative: l, preventScrollReset: u, viewTransition: d, defaultShouldRevalidate: f, ...p }, m) => {
	let { useTransitions: h } = _.useContext(at), g = Vn(), v = Hn(s, { relative: l }), y = o.toLowerCase() === "get" ? "get" : "post", b = typeof s == "string" && ee.test(s);
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
Pn.displayName = "Form";
function Fn(e) {
	return `${e} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`;
}
function In(e) {
	let t = _.useContext(Qe);
	return P(t, Fn(e)), t;
}
function Ln(e, { target: t, replace: n, mask: r, state: i, preventScrollReset: a, relative: o, viewTransition: s, defaultShouldRevalidate: c, useTransitions: l } = {}) {
	let u = yt(), d = gt(), f = St(e, { relative: o });
	return _.useCallback((p) => {
		if (tn(p, t)) {
			p.preventDefault();
			let t = n === void 0 ? ie(d) === ie(f) : n, m = () => u(e, {
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
function Rn(e) {
	F(typeof URLSearchParams < "u", "You cannot use the `useSearchParams` hook in a browser that does not support the URLSearchParams API. If you need to support Internet Explorer 11, we recommend you load a polyfill such as https://github.com/ungap/url-search-params.");
	let t = _.useRef(nn(e)), n = _.useRef(!1), r = gt(), i = _.useMemo(() => rn(r.search, n.current ? null : t.current), [r.search]), a = yt();
	return [i, _.useCallback((e, t) => {
		let r = nn(typeof e == "function" ? e(new URLSearchParams(i)) : e);
		n.current = !0, a("?" + r, t);
	}, [a, i])];
}
var zn = 0, Bn = () => `__${String(++zn)}__`;
function Vn() {
	let { router: e } = In("useSubmit"), { basename: t } = _.useContext(at), n = Lt(), r = e.fetch, i = e.navigate;
	return _.useCallback(async (e, a = {}) => {
		let { action: o, method: s, encType: c, formData: l, body: u } = ln(e, t);
		if (a.navigate === !1) {
			let e = a.fetcherKey || Bn();
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
function Hn(e, { relative: t } = {}) {
	let { basename: n } = _.useContext(at), r = _.useContext(st);
	P(r, "useFormAction must be used inside a RouteContext");
	let [i] = r.matches.slice(-1), a = { ...St(e || ".", { relative: t }) }, o = gt();
	if (e == null) {
		a.search = o.search;
		let e = new URLSearchParams(a.search), t = e.getAll("index");
		if (t.some((e) => e === "")) {
			e.delete("index"), t.filter((e) => e).forEach((t) => e.append("index", t));
			let n = e.toString();
			a.search = n ? `?${n}` : "";
		}
	}
	return (!e || e === ".") && i.route.index && (a.search = a.search ? a.search.replace(/^\?/, "?index&") : "?index"), n !== "/" && (a.pathname = a.pathname === "/" ? n : Ne([n, a.pathname])), ie(a);
}
function Un(e, { relative: t } = {}) {
	let n = _.useContext(nt);
	P(n != null, "`useViewTransitionState` must be used within `react-router-dom`'s `RouterProvider`.  Did you accidentally import `RouterProvider` from `react-router`?");
	let { basename: r } = In("useViewTransitionState"), i = St(e, { relative: t });
	if (!n.isTransitioning) return !1;
	let a = Te(n.currentLocation.pathname, r) || n.currentLocation.pathname, o = Te(n.nextLocation.pathname, r) || n.nextLocation.pathname;
	return xe(i.pathname, o) != null || xe(i.pathname, a) != null;
}
//#endregion
//#region node_modules/react/cjs/react-jsx-runtime.production.js
var Wn = /* @__PURE__ */ o(((e) => {
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
})), R = (/* @__PURE__ */ o(((e, t) => {
	t.exports = Wn();
})))(), Gn = (0, _.createContext)(null), Kn = 0;
function qn({ children: e }) {
	let t = (0, _.useSyncExternalStore)(C, S, S), [n, r] = (0, _.useState)(t?.user.role ?? "SUPPORT"), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(!1), [f, p] = (0, _.useState)(!1), [m, h] = (0, _.useState)([]), [g, v] = (0, _.useState)({}), y = (0, _.useCallback)((e) => {
		h((t) => t.filter((t) => t.id !== e));
	}, []), b = (0, _.useCallback)((e, t, n = "blue") => {
		Kn += 1;
		let r = Kn;
		h((i) => [...i.slice(-3), {
			id: r,
			title: e,
			desc: t,
			tone: n
		}]), window.setTimeout(() => y(r), 6e3);
	}, [y]), x = (0, _.useMemo)(() => {
		let e = t?.shipments ?? [];
		return Object.keys(g).length === 0 ? e : e.map((e) => g[e.id] ?? e);
	}, [t, g]), T = (0, _.useMemo)(() => t?.contracts ?? [], [t]), E = (0, _.useMemo)(() => t?.tasks ?? [], [t]), D = (0, _.useMemo)(() => t?.customers ?? [], [t]), O = (0, _.useMemo)(() => t?.quotes ?? [], [t]), k = (0, _.useMemo)(() => t?.agreements ?? [], [t]), ee = (0, _.useMemo)(() => t?.authority ?? {
		companies: [],
		agents: []
	}, [t]), j = (0, _.useMemo)(() => t?.notifications ?? [], [t]), M = (0, _.useMemo)(() => t?.home ?? null, [t]), N = (0, _.useMemo)(() => t?.environment ?? null, [t]), te = (0, _.useMemo)(() => t?.receivables ?? {
		rows: [],
		totals: {}
	}, [t]), P = (0, _.useMemo)(() => t?.payables ?? {
		rows: [],
		totals: {}
	}, [t]), F = (0, _.useMemo)(() => t?.ceoReport ?? null, [t]), ne = (0, _.useMemo)(() => t?.handbook ?? null, [t]), re = (0, _.useMemo)(() => t?.financeServiceCatalog ?? [], [t]), ie = (0, _.useCallback)((e, t) => A(e, t), []), ae = (0, _.useCallback)((e, n) => {
		let r = (t?.shipments ?? []).find((t) => t.id === e) ?? Object.values(g).find((t) => t.id === e);
		if (!r) return;
		let i = n(r);
		v((t) => ({
			...t,
			[e]: i
		})), A("shipment_update", { shipment: i });
	}, [t, g]), oe = t?.version, I = (0, _.useRef)(oe);
	oe !== I.current && (I.current = oe, t && v((e) => {
		let n = new Set((t.shipments ?? []).map((e) => e.id)), r = {};
		for (let [i, a] of Object.entries(e)) {
			let e = (t.shipments ?? []).find((e) => e.id === i);
			e && JSON.stringify(e) === JSON.stringify(a) || n.has(i) && (r[i] = a);
		}
		return r;
	}));
	let se = t?.user.name ?? "—", ce = (0, _.useMemo)(() => ({
		role: n,
		setRole: r,
		userName: se,
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
		agreements: k,
		authority: ee,
		tasks: E,
		notifications: j,
		home: M,
		environment: N,
		receivables: te,
		payables: P,
		ceoReport: F,
		handbook: ne,
		financeServices: re,
		unknownLabel: w(),
		dispatch: ie,
		updateShipment: ae
	}), [
		n,
		se,
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
		k,
		ee,
		E,
		j,
		M,
		N,
		te,
		P,
		F,
		ne,
		re,
		ie,
		ae
	]);
	return /* @__PURE__ */ (0, R.jsx)(Gn.Provider, {
		value: ce,
		children: e
	});
}
function Jn() {
	let e = (0, _.useContext)(Gn);
	if (!e) throw Error("useStore must be used inside <StoreProvider>");
	return e;
}
//#endregion
//#region src/lib/contractRoute.ts
function Yn(e) {
	return "/hop-dong/" + encodeURIComponent(e);
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toKebabCase.mjs
var Xn = (e) => e?.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toLucideIconData.mjs
function Zn(e, t, n = []) {
	if (t == null) throw Error("[lucide]: iconNode is required when icon name is used");
	return {
		name: Xn(e),
		size: 24,
		node: t,
		...n.length > 0 ? { aliases: n } : {}
	};
}
//#endregion
//#region node_modules/lucide-react/dist/esm/shared/src/utils/toCamelCase.mjs
var Qn = (e) => {
	let t = "", n = !1;
	for (let r of e) {
		if (r === "-" || r === "_" || r <= " ") {
			n = t.length > 0;
			continue;
		}
		t.length === 0 ? t += r.toLowerCase() : t += n ? r.toUpperCase() : r, n = !1;
	}
	return t;
}, $n = (e) => {
	let t = Qn(e);
	return t.charAt(0).toUpperCase() + t.slice(1);
}, er = (...e) => e.filter((e, t, n) => !!e && e.trim() !== "" && n.indexOf(e) === t).join(" ").trim(), tr = {
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
function nr(e) {
	return e != null;
}
function rr(e, t = {}) {
	let n = t.attributeNames ?? {}, r = (e) => n[e] ?? e, i = e.size ?? e.width ?? tr.width, a = e.size ?? e.height ?? tr.height, o = e.aliases?.filter((e) => typeof e == "string" && e.trim() !== "").map((e) => `lucide-${e}`) ?? [], s = [...e.name ? [`lucide-${e.name}`] : [], ...o], c = t.className?.split(" ").filter(Boolean) ?? [], l = t.includeDefaultClasses === !1 ? er(...c) : er("lucide", ...s, ...c), u = t.absoluteStrokeWidth ? Number(t.strokeWidth ?? tr["stroke-width"]) * Number(e.size ?? e.width ?? tr.width) / Number(t.size ?? t.width ?? tr.width) : t.strokeWidth ?? tr["stroke-width"];
	return [
		"svg",
		{
			...Object.entries(tr).reduce((e, [t, n]) => (e[r(t)] = n, e), {}),
			..."color" in t && t.color && { [r("stroke")]: t.color },
			..."size" in t && nr(t.size) && {
				[r("width")]: t.size,
				[r("height")]: t.size
			},
			..."width" in t && nr(t.width) && { [r("width")]: t.width },
			..."height" in t && nr(t.height) && { [r("height")]: t.height },
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
function ir(e, t = {}) {
	return rr(e, {
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
var ar = (e) => {
	for (let t in e) if (t.startsWith("aria-") || t === "role" || t === "title") return !0;
	return !1;
}, or = (0, _.createContext)({}), sr = () => (0, _.useContext)(or), cr = (0, _.forwardRef)(({ color: e, size: t, width: n, height: r, strokeWidth: i, absoluteStrokeWidth: a, nonScalingStroke: o, className: s = "", children: c, iconNode: l = [], icon: u = {
	node: l,
	aliases: [],
	size: 24
}, ...d }, f) => {
	let { size: p = 24, strokeWidth: m = 2, absoluteStrokeWidth: h = !1, nonScalingStroke: g = !1, color: v = "currentColor", className: y = "" } = sr() ?? {}, b = !!c || ar(d), [x, S, C = []] = ir(u, {
		color: e ?? v,
		width: n ?? t ?? p,
		height: r ?? t ?? p,
		strokeWidth: i ?? m,
		absoluteStrokeWidth: a ?? h,
		nonScalingStroke: o ?? g,
		className: er(y, s),
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
function z(e, t = [], n = []) {
	let r = typeof e == "string" ? Zn(e, t, n) : e, i = (0, _.forwardRef)(({ className: e, ...t }, n) => (0, _.createElement)(cr, {
		ref: n,
		icon: r,
		className: e,
		...t
	}));
	return r.name && (i.displayName = $n(r.name)), i;
}
//#endregion
//#region node_modules/lucide-react/dist/esm/icons/archive.mjs
var lr = {
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
lr.node;
var ur = z(lr), dr = {
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
dr.node;
var fr = z(dr), pr = {
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
pr.node;
var mr = z(pr), hr = {
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
hr.node;
var gr = z(hr), _r = {
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
_r.node;
var vr = z(_r), yr = {
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
yr.node;
var br = z(yr), xr = {
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
xr.node;
var Sr = z(xr), Cr = {
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
Cr.node;
var wr = z(Cr), Tr = {
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
Tr.node;
var Er = z(Tr), Dr = {
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
Dr.node;
var Or = z(Dr), kr = {
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
kr.node;
var Ar = z(kr), jr = {
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
jr.node;
var Mr = z(jr), Nr = {
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
Nr.node;
var Pr = z(Nr), Fr = {
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
Fr.node;
var Ir = z(Fr), Lr = {
	name: "check",
	size: 24,
	node: [["path", {
		d: "M20 6 9 17l-5-5",
		key: "1gmf2c"
	}]]
};
Lr.node;
var Rr = z(Lr), zr = {
	name: "chevron-down",
	size: 24,
	node: [["path", {
		d: "m6 9 6 6 6-6",
		key: "qrunsl"
	}]]
};
zr.node;
var Br = z(zr), Vr = {
	name: "chevron-right",
	size: 24,
	node: [["path", {
		d: "m9 18 6-6-6-6",
		key: "mthhwq"
	}]]
};
Vr.node;
var Hr = z(Vr), Ur = {
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
var Wr = z(Ur), Gr = {
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
var Kr = z(Gr), qr = {
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
var Jr = z(qr), Yr = {
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
var Xr = z(Yr), Zr = {
	name: "clipboard-paste",
	size: 24,
	node: [
		["path", {
			d: "M11 14h10",
			key: "1w8e9d"
		}],
		["path", {
			d: "M16 4h2a2 2 0 0 1 2 2v1.344",
			key: "1e62lh"
		}],
		["path", {
			d: "m17 18 4-4-4-4",
			key: "z2g111"
		}],
		["path", {
			d: "M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 1.793-1.113",
			key: "bjbb7m"
		}],
		["rect", {
			x: "8",
			y: "2",
			width: "8",
			height: "4",
			rx: "1",
			key: "ublpy"
		}]
	]
};
Zr.node;
var Qr = z(Zr), $r = {
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
$r.node;
var ei = z($r), ti = {
	name: "cloud-upload",
	size: 24,
	node: [
		["path", {
			d: "M12 13v8",
			key: "1l5pq0"
		}],
		["path", {
			d: "M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242",
			key: "1pljnt"
		}],
		["path", {
			d: "m8 17 4-4 4 4",
			key: "1quai1"
		}]
	],
	aliases: ["upload-cloud"]
};
ti.node;
var ni = z(ti), ri = {
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
ri.node;
var ii = z(ri), ai = {
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
ai.node;
var oi = z(ai), si = {
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
si.node;
var ci = z(si), li = {
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
li.node;
var ui = z(li), di = {
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
di.node;
var fi = z(di), pi = {
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
pi.node;
var mi = z(pi), hi = {
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
hi.node;
var gi = z(hi), _i = {
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
_i.node;
var vi = z(_i), yi = {
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
yi.node;
var bi = z(yi), xi = {
	name: "file-spreadsheet",
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
			d: "M8 13h2",
			key: "yr2amv"
		}],
		["path", {
			d: "M14 13h2",
			key: "un5t4a"
		}],
		["path", {
			d: "M8 17h2",
			key: "2yhykz"
		}],
		["path", {
			d: "M14 17h2",
			key: "10kma7"
		}]
	]
};
xi.node;
var Si = z(xi), Ci = {
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
Ci.node;
var wi = z(Ci), Ti = {
	name: "folder-x",
	size: 24,
	node: [
		["path", {
			d: "M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z",
			key: "1kt360"
		}],
		["path", {
			d: "m9.5 10.5 5 5",
			key: "ra9qjz"
		}],
		["path", {
			d: "m14.5 10.5-5 5",
			key: "l2rkpq"
		}]
	]
};
Ti.node;
var Ei = z(Ti), Di = {
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
Di.node;
var Oi = z(Di), ki = {
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
ki.node;
var Ai = z(ki), ji = {
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
ji.node;
var Mi = z(ji), Ni = {
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
Ni.node;
var B = z(Ni), Pi = {
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
Pi.node;
var Fi = z(Pi), Ii = {
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
Ii.node;
var Li = z(Ii), Ri = {
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
Ri.node;
var zi = z(Ri), Bi = {
	name: "list-todo",
	size: 24,
	node: [
		["path", {
			d: "M13 5h8",
			key: "a7qcls"
		}],
		["path", {
			d: "M13 12h8",
			key: "h98zly"
		}],
		["path", {
			d: "M13 19h8",
			key: "c3s6r1"
		}],
		["path", {
			d: "m3 17 2 2 4-4",
			key: "1jhpwq"
		}],
		["rect", {
			x: "3",
			y: "4",
			width: "6",
			height: "6",
			rx: "1",
			key: "cif1o7"
		}]
	]
};
Bi.node;
var Vi = z(Bi), Hi = {
	name: "loader-circle",
	size: 24,
	node: [["path", {
		d: "M21 12a9 9 0 1 1-6.219-8.56",
		key: "13zald"
	}]],
	aliases: ["loader-2"]
};
Hi.node;
var Ui = z(Hi), Wi = {
	name: "lock-open",
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
		d: "M7 11V7a5 5 0 0 1 9.9-1",
		key: "1mm8w8"
	}]],
	aliases: ["unlock"]
};
Wi.node;
var Gi = z(Wi), Ki = {
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
Ki.node;
var qi = z(Ki), Ji = {
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
Ji.node;
var Yi = z(Ji), Xi = {
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
Xi.node;
var Zi = z(Xi), Qi = {
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
Qi.node;
var $i = z(Qi), ea = {
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
ea.node;
var ta = z(ea), na = {
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
na.node;
var ra = z(na), ia = {
	name: "paperclip",
	size: 24,
	node: [["path", {
		d: "m16 6-8.414 8.586a2 2 0 0 0 2.829 2.829l8.414-8.586a4 4 0 1 0-5.657-5.657l-8.379 8.551a6 6 0 1 0 8.485 8.485l8.379-8.551",
		key: "1miecu"
	}]]
};
ia.node;
var aa = z(ia), oa = {
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
oa.node;
var sa = z(oa), ca = {
	name: "pencil-line",
	size: 24,
	node: [
		["path", {
			d: "M13 21h8",
			key: "1jsn5i"
		}],
		["path", {
			d: "m15 5 4 4",
			key: "1mk7zo"
		}],
		["path", {
			d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
			key: "1a8usu"
		}]
	]
};
ca.node;
var la = z(ca), ua = {
	name: "phone",
	size: 24,
	node: [["path", {
		d: "M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384",
		key: "9njp5v"
	}]]
};
ua.node;
var da = z(ua), fa = {
	name: "plane",
	size: 24,
	node: [["path", {
		d: "M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z",
		key: "1v9wt8"
	}]]
};
fa.node;
var pa = z(fa), ma = {
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
ma.node;
var ha = z(ma), ga = {
	name: "receipt",
	size: 24,
	node: [
		["path", {
			d: "M12 17V7",
			key: "pyj7ub"
		}],
		["path", {
			d: "M16 8h-6a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H8",
			key: "1elt7d"
		}],
		["path", {
			d: "M4 3a1 1 0 0 1 1-1 1.3 1.3 0 0 1 .7.2l.933.6a1.3 1.3 0 0 0 1.4 0l.934-.6a1.3 1.3 0 0 1 1.4 0l.933.6a1.3 1.3 0 0 0 1.4 0l.933-.6a1.3 1.3 0 0 1 1.4 0l.934.6a1.3 1.3 0 0 0 1.4 0l.933-.6A1.3 1.3 0 0 1 19 2a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1 1.3 1.3 0 0 1-.7-.2l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.934.6a1.3 1.3 0 0 1-1.4 0l-.933-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-1.4 0l-.934-.6a1.3 1.3 0 0 0-1.4 0l-.933.6a1.3 1.3 0 0 1-.7.2 1 1 0 0 1-1-1z",
			key: "ycz6yz"
		}]
	]
};
ga.node;
var _a = z(ga), va = {
	name: "rotate-ccw-key",
	size: 24,
	node: [
		["path", {
			d: "M12 7v6",
			key: "lw1j43"
		}],
		["path", {
			d: "M12 9h2",
			key: "1lpap9"
		}],
		["path", {
			d: "M3 12a9 9 0 1 0 9-9 9.74 9.74 0 0 0-6.74 2.74L3 8",
			key: "g2jlw"
		}],
		["path", {
			d: "M3 3v5h5",
			key: "1xhq8a"
		}],
		["circle", {
			cx: "12",
			cy: "15",
			r: "2",
			key: "1vpstw"
		}]
	]
};
va.node;
var ya = z(va), ba = {
	name: "save",
	size: 24,
	node: [
		["path", {
			d: "M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
			key: "1c8476"
		}],
		["path", {
			d: "M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7",
			key: "1ydtos"
		}],
		["path", {
			d: "M7 3v4a1 1 0 0 0 1 1h7",
			key: "t51u73"
		}]
	]
};
ba.node;
var xa = z(ba), Sa = {
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
Sa.node;
var Ca = z(Sa), wa = {
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
wa.node;
var Ta = z(wa), Ea = {
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
Ea.node;
var Da = z(Ea), Oa = {
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
Oa.node;
var ka = z(Oa), Aa = {
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
Aa.node;
var ja = z(Aa), Ma = {
	name: "ship",
	size: 24,
	node: [
		["path", {
			d: "M12 2v2",
			key: "tus03m"
		}],
		["path", {
			d: "M12 9.189V13",
			key: "yp40p3"
		}],
		["path", {
			d: "M19 12V6a2 2 0 00-2-2H7a2 2 0 00-2 2v6",
			key: "1wcigf"
		}],
		["path", {
			d: "M19.38 19A11.6 11.6 0 0021 13l-8.188-3.639a2 2 0 00-1.624 0L3 13.001a11.6 11.6 0 002.81 7.76",
			key: "1kdp0u"
		}],
		["path", {
			d: "M2 20c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1",
			key: "1l8w7g"
		}]
	]
};
Ma.node;
var Na = z(Ma), Pa = {
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
Pa.node;
var Fa = z(Pa), Ia = {
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
Ia.node;
var La = z(Ia), Ra = {
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
Ra.node;
var za = z(Ra), Ba = {
	name: "train-front",
	size: 24,
	node: [
		["path", {
			d: "M8 3.1V7a4 4 0 0 0 8 0V3.1",
			key: "1v71zp"
		}],
		["path", {
			d: "m9 15-1-1",
			key: "1yrq24"
		}],
		["path", {
			d: "m15 15 1-1",
			key: "1t0d6s"
		}],
		["path", {
			d: "M9 19c-2.8 0-5-2.2-5-5v-4a8 8 0 0 1 16 0v4c0 2.8-2.2 5-5 5Z",
			key: "1p0hjs"
		}],
		["path", {
			d: "m8 19-2 3",
			key: "13i0xs"
		}],
		["path", {
			d: "m16 19 2 3",
			key: "xo31yx"
		}]
	]
};
Ba.node;
var Va = z(Ba), Ha = {
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
Ha.node;
var Ua = z(Ha), Wa = {
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
Wa.node;
var Ga = z(Wa), Ka = {
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
Ka.node;
var qa = z(Ka), Ja = {
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
Ja.node;
var Ya = z(Ja), Xa = {
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
Xa.node;
var Za = z(Xa), Qa = {
	name: "user-plus",
	size: 24,
	node: [
		["path", {
			d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",
			key: "1yyitq"
		}],
		["circle", {
			cx: "9",
			cy: "7",
			r: "4",
			key: "nufk8"
		}],
		["line", {
			x1: "19",
			x2: "19",
			y1: "8",
			y2: "14",
			key: "1bvyxn"
		}],
		["line", {
			x1: "22",
			x2: "16",
			y1: "11",
			y2: "11",
			key: "1shjgl"
		}]
	]
};
Qa.node;
var $a = z(Qa), eo = {
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
eo.node;
var to = z(eo), no = {
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
no.node;
var ro = z(no), io = {
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
io.node;
var ao = z(io), oo = {
	ADMIN: "Quản trị",
	SUPPORT: "Điều phối",
	SALE: "Kinh doanh"
}, so = [
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
				label: "Đại Lý Trường Thành",
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
], co = {
	shipments: [],
	contracts: [],
	customers: [],
	quotes: [],
	tasks: [],
	notifs: []
};
function V(e, t) {
	e.length = 0, Array.isArray(t) && e.push(...t);
}
C(() => {
	let e = S();
	e && (V(co.shipments, e.shipments), V(co.contracts, e.contracts), V(co.customers, e.customers), V(co.quotes, e.quotes), V(co.tasks, e.tasks), V(co.notifs, e.notifications));
});
{
	let e = S();
	e && (V(co.shipments, e.shipments), V(co.contracts, e.contracts), V(co.customers, e.customers), V(co.quotes, e.quotes), V(co.tasks, e.tasks), V(co.notifs, e.notifications));
}
var lo = co.shipments, uo = co.contracts, H = co.customers, fo = co.quotes, po = co.tasks;
co.notifs;
//#endregion
//#region src/lib/format.ts
function U(...e) {
	return e.filter(Boolean).join(" ");
}
function mo(e) {
	return e == null || e === "" || typeof e == "number" && Number.isNaN(e);
}
function W(e, t) {
	if (mo(e)) return "—";
	let n = Number(e);
	return Number.isNaN(n) ? "—" : n.toLocaleString("vi-VN");
}
function ho(e) {
	return mo(e) ? "— ₫" : `${W(e)} ₫`;
}
function G(e, t) {
	let n = (t || "VND").toUpperCase();
	return mo(e) ? `— ${n}` : `${W(e)} ${n}`;
}
function go(e, t) {
	let n = (t || "VND").toUpperCase();
	return mo(e) ? `— tr ${n}` : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr ${n}`;
}
function _o(e) {
	return mo(e) ? "—" : `${Number(e).toLocaleString("vi-VN", { maximumFractionDigits: 2 })}%`;
}
function vo(e) {
	return mo(e) ? "— tr" : `${(Number(e) / 1e6).toLocaleString("vi-VN")} tr`;
}
function yo(e) {
	if (e == null) return null;
	if (typeof e == "number") return Number.isFinite(e) ? e : null;
	let t = String(e).replace(/[^\d.,-]/g, "");
	if (!t || !/\d/.test(t)) return null;
	let n = t.lastIndexOf(","), r = t.lastIndexOf("."), i = (t.match(/,/g) || []).length, a = (t.match(/\./g) || []).length, o = t;
	if (i > 0 && a > 0) {
		let e = n > r ? "," : ".", i = e === "," ? "." : ",";
		o = (t.split(e).pop() ?? "").length <= 2 ? t.split(i).join("").replace(e, ".") : t.replace(/[.,]/g, "");
	} else if (i > 1 || a > 1) o = t.replace(/[.,]/g, "");
	else if (i === 1) {
		let [e, n = ""] = t.split(",");
		o = n.length <= 2 ? `${e.replace(/,/g, "")}.${n}` : t.replace(/,/g, "");
	} else if (a === 1) {
		let [e, n = ""] = t.split(".");
		n.length === 3 && e.replace("-", "").length >= 1 && (o = t.replace(/\./g, ""));
	}
	let s = Number(o);
	return Number.isFinite(s) ? s : null;
}
function bo(e) {
	if (mo(e)) return "—";
	let t = Number(e);
	return Number.isNaN(t) ? String(e) : t.toLocaleString("vi-VN");
}
function K(e) {
	let t = (e ?? "").trim();
	return t.length > 0 ? t : "—";
}
function xo(e, t, n) {
	if (!t) return;
	let r = atob(t), i = new Uint8Array(r.length);
	for (let e = 0; e < r.length; e += 1) i[e] = r.charCodeAt(e);
	let a = new Blob([i], { type: n }), o = URL.createObjectURL(a), s = document.createElement("a");
	s.href = o, s.download = e, document.body.appendChild(s), s.click(), document.body.removeChild(s), setTimeout(() => URL.revokeObjectURL(o), 4e3);
}
//#endregion
//#region src/components/ui.tsx
var So = {
	layout: Fi,
	alarm: Er,
	box: ra,
	plus: Jr,
	truck: qa,
	users: to,
	handshake: Oi,
	calc: Pr,
	filecheck: gi,
	filetext: wi,
	wallet: ro,
	scale: Ca,
	building: Mr,
	chart: Ir,
	search: Ta,
	book: Ar,
	lang: B,
	shield: ka
};
function q({ tone: e, children: t, size: n = "md" }) {
	return /* @__PURE__ */ (0, R.jsx)("span", {
		className: U("inline-flex items-center gap-1.5 font-semibold border rounded-full whitespace-nowrap", n === "sm" ? "text-[12.5px] px-2.5 py-1" : "text-[13.5px] px-3 py-1.5", {
			green: "bg-emerald-50 text-emerald-800 border-emerald-200",
			amber: "bg-amber-50 text-amber-900 border-amber-200",
			red: "bg-red-50 text-red-800 border-red-200",
			blue: "bg-blue-50 text-blue-800 border-blue-200",
			gray: "bg-slate-100 text-slate-700 border-slate-200"
		}[e]),
		children: t
	});
}
function Co({ tone: e }) {
	return /* @__PURE__ */ (0, R.jsx)("span", { className: U("inline-block w-2.5 h-2.5 rounded-full shrink-0", {
		green: "bg-emerald-500",
		amber: "bg-amber-500",
		red: "bg-red-500",
		blue: "bg-blue-500",
		gray: "bg-slate-400"
	}[e] ?? "bg-slate-400") });
}
function J({ icon: e, title: t, sub: n, right: r }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "flex items-start justify-between gap-3 mb-3",
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex items-start gap-2.5",
			children: [e && /* @__PURE__ */ (0, R.jsx)("span", {
				className: "mt-0.5 w-9 h-9 rounded-xl bg-[#0f2a4a] text-white grid place-items-center shrink-0",
				children: e
			}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("h2", {
				className: "text-[17px] md:text-[19px] font-800 font-extrabold text-[#0f2a4a] leading-tight",
				children: t
			}), n && /* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-[13.5px] text-slate-500 mt-0.5",
				children: n
			})] })]
		}), r]
	});
}
function Y({ label: e, required: t, hint: n, error: r, children: i }) {
	return /* @__PURE__ */ (0, R.jsxs)("label", {
		className: "block",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("span", {
				className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
				children: [
					e,
					" ",
					t && /* @__PURE__ */ (0, R.jsx)("span", {
						className: "text-red-600 font-bold",
						children: "*"
					})
				]
			}),
			i,
			n && !r && /* @__PURE__ */ (0, R.jsx)("span", {
				className: "block text-[13px] text-slate-500 mt-1",
				children: n
			}),
			r && /* @__PURE__ */ (0, R.jsxs)("span", {
				className: "block text-[13.5px] text-red-700 font-medium mt-1",
				children: ["⚠ ", r]
			})
		]
	});
}
var X = (e) => U("w-full rounded-xl border-2 bg-white px-3.5 text-[15.5px] min-h-[48px] py-2.5 placeholder:text-slate-400 transition-colors", e === "missing" && "border-amber-400 bg-amber-50/60", e === "invalid" && "border-red-400 bg-red-50/60", (!e || e === "ok") && "border-slate-200 focus:border-[#1e5aa8]");
function wo({ children: e, onClick: t, className: n, disabled: r, testId: i }) {
	return /* @__PURE__ */ (0, R.jsx)("button", {
		onClick: t,
		disabled: r,
		...i ? { "data-testid": i } : {},
		className: U("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] hover:bg-[#14365e] text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-navy-900/20 disabled:opacity-50 disabled:cursor-not-allowed", n),
		children: e
	});
}
function To({ children: e, onClick: t, className: n, disabled: r, testId: i }) {
	return /* @__PURE__ */ (0, R.jsx)("button", {
		onClick: t,
		disabled: r,
		...i ? { "data-testid": i } : {},
		className: U("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-emerald-600/25 disabled:opacity-50 disabled:cursor-not-allowed", n),
		children: e
	});
}
function Eo({ children: e, onClick: t, className: n, danger: r, disabled: i, testId: a }) {
	return /* @__PURE__ */ (0, R.jsx)("button", {
		onClick: t,
		disabled: i,
		...a ? { "data-testid": a } : {},
		className: U("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 font-semibold text-[15px] px-4 min-h-[48px] bg-white disabled:opacity-50 disabled:cursor-not-allowed", r ? "border-red-200 text-red-700 hover:bg-red-50" : "border-slate-200 text-[#0f2a4a] hover:bg-slate-50", n),
		children: e
	});
}
function Do({ tone: e = "amber", title: t, desc: n, action: r, onAction: i }) {
	let a = {
		amber: "border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50/60",
		red: "border-red-300 bg-gradient-to-r from-red-50 to-orange-50/60",
		green: "border-emerald-300 bg-gradient-to-r from-emerald-50 to-teal-50/60",
		blue: "border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50/60"
	}, o = e === "red" ? $i : e === "green" ? Kr : e === "blue" ? Ai : Ga, s = e === "red" ? "bg-red-600" : e === "green" ? "bg-emerald-600" : e === "blue" ? "bg-blue-600" : "bg-amber-500";
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: U("rounded-2xl border-2 p-4 md:p-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-4", a[e]),
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex items-start gap-3 flex-1 min-w-0",
			children: [/* @__PURE__ */ (0, R.jsx)("span", {
				className: U("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", s),
				children: /* @__PURE__ */ (0, R.jsx)(o, { size: 22 })
			}), /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "min-w-0",
				children: [
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[12.5px] font-bold uppercase tracking-wide text-slate-500",
						children: "Việc tiếp theo"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[16px] md:text-[18px] font-extrabold text-[#0f2a4a] leading-snug",
						children: t
					}),
					n && /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-600 mt-1",
						children: n
					})
				]
			})]
		}), r && /* @__PURE__ */ (0, R.jsxs)("button", {
			onClick: i,
			className: "btn-press touch-target shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[15.5px] px-6 min-h-[52px] shadow-lg w-full md:w-auto",
			children: [
				r,
				" ",
				/* @__PURE__ */ (0, R.jsx)(gr, { size: 18 })
			]
		})]
	});
}
function Oo({ what: e, where: t, actionLabel: n, onAction: r }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-xl border-2 border-dashed border-amber-400 bg-amber-50 p-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5",
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex items-start gap-2 flex-1",
			children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
				size: 20,
				className: "text-amber-600 shrink-0 mt-0.5"
			}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "font-bold text-[15px] text-amber-900",
				children: ["Thiếu ", e]
			}), t && /* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-[13.5px] text-amber-800",
				children: t
			})] })]
		}), /* @__PURE__ */ (0, R.jsxs)("button", {
			onClick: r,
			className: "btn-press touch-target inline-flex items-center justify-center gap-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-[14.5px] font-bold px-4 min-h-[44px] whitespace-nowrap",
			children: [
				/* @__PURE__ */ (0, R.jsx)(sa, { size: 16 }),
				" ",
				n
			]
		})]
	});
}
function ko({ id: e, labelledBy: t, onClose: n, pending: r, children: i, testId: a, width: o = 480 }) {
	let s = (0, _.useRef)(null);
	return (0, _.useEffect)(() => {
		let e = s.current;
		if (!e) return;
		let t = e.getRootNode().activeElement;
		return (e.querySelector("input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])") ?? e).focus(), () => {
			t?.isConnected && t.focus();
		};
	}, []), (0, _.useEffect)(() => {
		let e = s.current;
		if (!e) return;
		let t = e.getRootNode(), i = () => Array.from(e.querySelectorAll("a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex=\"-1\"])")), a = (a) => {
			let o = a;
			if (o.key === "Escape") {
				o.preventDefault(), o.stopPropagation(), r || n();
				return;
			}
			if (o.key !== "Tab") return;
			let s = i();
			if (s.length === 0) {
				o.preventDefault(), e.focus();
				return;
			}
			let c = s[0], l = s[s.length - 1], u = t.activeElement, d = !u || !e.contains(u);
			o.shiftKey ? (u === c || d) && (o.preventDefault(), l.focus()) : (u === l || d) && (o.preventDefault(), c.focus());
		};
		return t.addEventListener("keydown", a, !0), () => t.removeEventListener("keydown", a, !0);
	}, [r, n]), /* @__PURE__ */ (0, R.jsxs)("div", {
		...e ? { id: e } : {},
		className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
		...a ? { "data-testid": a } : {},
		children: [/* @__PURE__ */ (0, R.jsx)("div", {
			className: "absolute inset-0 bg-slate-900/55 anim-fade",
			"aria-hidden": "true",
			onClick: r ? void 0 : n
		}), /* @__PURE__ */ (0, R.jsx)("div", {
			ref: s,
			role: "dialog",
			"aria-modal": "true",
			"aria-labelledby": t,
			tabIndex: -1,
			className: "relative bg-white w-full rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up outline-none",
			style: { maxWidth: o },
			children: i
		})]
	});
}
function Ao({ label: e, value: t, big: n }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "flex items-start justify-between gap-3 py-2 border-b border-slate-100 last:border-0",
		children: [/* @__PURE__ */ (0, R.jsx)("span", {
			className: "text-[13.5px] text-slate-500 font-medium shrink-0 pt-0.5",
			children: e
		}), /* @__PURE__ */ (0, R.jsx)("span", {
			className: U("text-right font-semibold text-slate-800", n ? "text-[17px]" : "text-[14.5px]"),
			children: t
		})]
	});
}
function jo({ label: e, testId: t, options: n, selectedId: r, selectedLabel: i, placeholder: a, emptyHint: o, required: s, onSelect: c }) {
	let [l, u] = (0, _.useState)(!1), [d, f] = (0, _.useState)(""), p = d.trim().toLowerCase(), m = p ? n.filter((e) => (e.id + e.label + (e.sub ?? "")).toLowerCase().includes(p)) : n, h = (e) => {
		c(e), f(""), u(!1);
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-xl border-2 border-slate-200 bg-white p-2.5",
		"data-testid": t,
		"data-selected": r || "",
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex items-start justify-between gap-2",
			children: [/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "min-w-0",
				children: [/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
					children: [e, s ? " *" : ""]
				}), /* @__PURE__ */ (0, R.jsx)("p", {
					className: U("truncate text-[14.5px] font-semibold mt-0.5", r ? "text-slate-800" : "text-slate-400"),
					"data-testid": `${t}-value`,
					children: i || r || "— chưa chọn —"
				})]
			}), /* @__PURE__ */ (0, R.jsxs)("button", {
				type: "button",
				onClick: () => u((e) => !e),
				"aria-expanded": l,
				className: U("btn-press touch-target shrink-0 inline-flex items-center gap-1.5 rounded-lg border-2 px-3 min-h-[40px] text-[13px] font-bold", l ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
				"data-testid": `${t}-toggle`,
				children: [
					/* @__PURE__ */ (0, R.jsx)(Ta, { size: 15 }),
					" ",
					l ? "Đóng" : "Tìm / đổi"
				]
			})]
		}), l && /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "mt-2.5 space-y-2",
			"data-testid": `${t}-panel`,
			children: [/* @__PURE__ */ (0, R.jsx)("input", {
				value: d,
				onChange: (e) => f(e.target.value),
				placeholder: a ?? "Gõ tên hoặc mã để tìm…",
				className: X(),
				"aria-label": `Tìm ${e.toLowerCase()}`,
				"data-testid": `${t}-search`
			}), n.length === 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
				className: "rounded-lg bg-amber-50 px-2.5 py-2 text-[13px] font-semibold text-amber-800",
				"data-testid": `${t}-empty`,
				children: o ?? "Danh bạ đang trống — chưa có gì để chọn."
			}) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "text-[12.5px] text-slate-500",
				"data-testid": `${t}-count`,
				children: [
					"Thấy ",
					/* @__PURE__ */ (0, R.jsx)("b", {
						className: "text-[#0f2a4a]",
						children: m.length
					}),
					"/",
					n.length,
					p ? ` cho “${d.trim()}”` : null
				]
			}), /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "max-h-[240px] overflow-y-auto space-y-1",
				"data-testid": `${t}-list`,
				children: [m.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
					type: "button",
					onClick: () => h(e.id),
					className: U("btn-press touch-target w-full rounded-lg border-2 px-2.5 py-2 text-left text-[13.5px] font-semibold", e.id === r ? "border-[#0f2a4a] bg-[#eef4fb] text-[#0f2a4a]" : "border-slate-200 bg-white text-slate-700"),
					"data-testid": `${t}-option-${e.id}`,
					children: [/* @__PURE__ */ (0, R.jsx)("span", {
						className: "block truncate",
						children: e.label
					}), /* @__PURE__ */ (0, R.jsx)("span", {
						className: "block text-[12px] font-medium text-slate-400",
						children: e.sub ?? e.id
					})]
				}, e.id)), m.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "rounded-lg bg-slate-50 px-2.5 py-2 text-[13px] font-semibold text-slate-500",
					"data-testid": `${t}-nomatch`,
					children: [
						"Không có mục nào khớp “",
						d.trim(),
						"”."
					]
				})]
			})] })]
		})]
	});
}
function Mo({ value: e, onChange: t, testId: n, stored: r }) {
	let i = [
		{
			key: "YES",
			label: "Có PL"
		},
		{
			key: "NO",
			label: "Không cần PL"
		},
		{
			key: "",
			label: "Chưa chọn"
		}
	], a = e === "YES" || e === "NO" ? e : "";
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-1.5",
		"data-testid": n,
		children: [/* @__PURE__ */ (0, R.jsxs)("p", {
			className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
			children: ["Phụ lục (PL)", r ? ` · đang lưu: ${r}` : ""]
		}), /* @__PURE__ */ (0, R.jsx)("div", {
			className: "flex flex-wrap gap-1.5",
			children: i.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
				type: "button",
				onClick: () => t(e.key),
				"aria-pressed": a === e.key,
				className: U("btn-press touch-target rounded-lg border-2 px-3 min-h-[40px] text-[13.5px] font-bold", a === e.key ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
				"data-testid": `${n}-${e.key || "unknown"}`,
				children: e.label
			}, e.key || "unknown"))
		})]
	});
}
//#endregion
//#region src/components/Layout.tsx
function No({ sandbox: e, displayName: t }) {
	return /* @__PURE__ */ (0, R.jsxs)(L, {
		to: "/",
		className: "flex items-center gap-2.5 shrink-0",
		children: [
			/* @__PURE__ */ (0, R.jsx)("span", {
				className: "w-10 h-10 rounded-xl bg-gradient-to-br from-[#1e5aa8] to-[#0a1f3a] grid place-items-center text-white font-extrabold text-[18px] shadow",
				children: "T"
			}),
			/* @__PURE__ */ (0, R.jsxs)("span", {
				className: "leading-tight hidden sm:block",
				children: [/* @__PURE__ */ (0, R.jsx)("span", {
					className: "block font-extrabold text-[14.5px] text-[#0f2a4a]",
					children: "TRƯỜNG THÀNH"
				}), /* @__PURE__ */ (0, R.jsx)("span", {
					className: "block text-[11.5px] text-slate-500 font-medium",
					children: t ? `${t} · Nội bộ` : "Nội bộ"
				})]
			}),
			e && /* @__PURE__ */ (0, R.jsx)("span", {
				className: "text-[11px] font-extrabold tracking-wider bg-violet-100 text-violet-800 border border-violet-300 rounded-md px-1.5 py-0.5 ml-1",
				children: "PROTOTYPE"
			})
		]
	});
}
function Po({ children: e }) {
	let { role: t, setRole: n, userName: r, query: i, setQuery: a, searchOpen: o, setSearchOpen: s, navOpen: c, setNavOpen: l, notifOpen: u, setNotifOpen: d, quickAddOpen: f, setQuickAddOpen: p, toasts: m, dismissToast: h, toast: g, notifications: v, tasks: y, environment: b } = Jn(), x = v, S = x.length, C = y.filter((e) => e.level === "Khan" || e.level === "CanXuLy").length, w = yt(), T = gt(), [E, D] = (0, _.useState)(!1), O = (0, _.useMemo)(() => {
		let e = i.trim().toLowerCase();
		return e.length < 2 ? null : {
			lots: lo.filter((t) => (t.id + t.customer + t.contract + t.route).toLowerCase().includes(e)).slice(0, 4),
			cts: uo.filter((t) => (t.id + t.company + t.agent).toLowerCase().includes(e)).slice(0, 3),
			cus: H.filter((t) => (t.name + t.mst).toLowerCase().includes(e)).slice(0, 3),
			quo: fo.filter((t) => (t.id + t.customer).toLowerCase().includes(e)).slice(0, 2)
		};
	}, [i]), k = (e) => {
		s(!1), a(""), w(e), l(!1);
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "min-h-screen flex flex-col",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("header", {
				className: "no-print sticky top-0 z-40 bg-white border-b border-slate-200 shadow-[0_1px_12px_rgba(15,42,74,.08)]",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "flex items-center gap-2 md:gap-4 px-3 md:px-5 h-[64px] max-w-[1600px] mx-auto",
					children: [
						/* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => l(!0),
							className: "lg:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Mở menu",
							children: /* @__PURE__ */ (0, R.jsx)(Zi, {
								size: 22,
								className: "text-[#0f2a4a]"
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(No, {
							sandbox: b?.isSandbox === !0,
							displayName: b?.displayName
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "hidden md:flex flex-1 max-w-[560px] mx-auto relative",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center w-full rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ta, {
										size: 19,
										className: "ml-3.5 text-slate-400 shrink-0"
									}),
									/* @__PURE__ */ (0, R.jsx)("input", {
										value: i,
										onChange: (e) => a(e.target.value),
										onFocus: () => s(!0),
										placeholder: "Tìm mã lô · khách hàng · hợp đồng · container · báo giá…",
										className: "w-full bg-transparent px-3 py-2.5 text-[15px] outline-none placeholder:text-slate-400"
									}),
									i && /* @__PURE__ */ (0, R.jsx)("button", {
										onClick: () => a(""),
										className: "mr-2 w-8 h-8 grid place-items-center rounded-lg hover:bg-slate-200",
										children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 16 })
									})
								]
							}), o && O && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "absolute top-[52px] left-0 right-0 bg-white rounded-2xl border border-slate-200 shadow-2xl p-2 z-50 anim-slide-up max-h-[70vh] overflow-auto",
								children: [
									O.lots.length + O.cts.length + O.cus.length + O.quo.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
										className: "p-4 text-[14.5px] text-slate-500",
										children: [
											"Không tìm thấy “",
											i,
											"”. Thử lại theo ",
											/* @__PURE__ */ (0, R.jsx)("b", { children: "mã lô" }),
											", ",
											/* @__PURE__ */ (0, R.jsx)("b", { children: "tên khách hàng" }),
											" hoặc ",
											/* @__PURE__ */ (0, R.jsx)("b", { children: "số hợp đồng" }),
											" đang có trong hệ thống."
										]
									}),
									O.lots.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => k(`/lo-hang/${e.id}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-blue-100 grid place-items-center",
											children: /* @__PURE__ */ (0, R.jsx)(ra, {
												size: 17,
												className: "text-blue-700"
											})
										}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.customer
											]
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Lô hàng — ", e.status]
										})] })]
									}, e.id)),
									O.cts.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => k(Yn(e.id)),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-emerald-100 grid place-items-center",
											children: /* @__PURE__ */ (0, R.jsx)(wi, {
												size: 17,
												className: "text-emerald-700"
											})
										}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.company
											]
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Hợp đồng — ", e.status]
										})] })]
									}, e.id)),
									O.cus.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => k(`/khach-hang?q=${encodeURIComponent(e.name || e.short || e.mst)}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-amber-100 grid place-items-center",
											children: /* @__PURE__ */ (0, R.jsx)(qa, {
												size: 17,
												className: "text-amber-700"
											})
										}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.short,
												" · MST ",
												e.mst
											]
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: "Khách hàng"
										})] })]
									}, e.mst)),
									O.quo.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => k(`/kinh-doanh-bao-gia?q=${encodeURIComponent(e.id)}`),
										className: "w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "w-9 h-9 rounded-lg bg-violet-100 grid place-items-center",
											children: /* @__PURE__ */ (0, R.jsx)(Pr, {
												size: 17,
												className: "text-violet-700"
											})
										}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14.5px] text-[#0f2a4a]",
											children: [
												e.id,
												" · ",
												e.customer
											]
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: ["Báo giá — ", e.status]
										})] })]
									}, e.id)),
									/* @__PURE__ */ (0, R.jsx)("button", {
										onClick: () => s(!1),
										className: "w-full text-center py-2 text-[13px] text-slate-400 font-medium",
										children: "Nhấn ra ngoài để đóng"
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", { className: "flex-1 md:hidden" }),
						/* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => s(!o),
							className: "md:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Tìm kiếm",
							children: /* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 21,
								className: "text-[#0f2a4a]"
							})
						}),
						b?.isSandbox ? /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "relative hidden sm:block",
							"data-testid": "role-preview-switcher",
							children: [/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => D((e) => !e),
								"aria-haspopup": "menu",
								"aria-expanded": E,
								className: "flex items-center gap-2 rounded-xl border-2 border-slate-200 pl-1.5 pr-2.5 py-1 hover:border-[#1e5aa8]",
								children: [
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: U("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", t === "ADMIN" ? "bg-violet-600" : t === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600"),
										children: r.charAt(0)
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "text-left leading-tight",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "block text-[13px] font-bold text-[#0f2a4a]",
											children: r
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[11.5px] text-slate-500",
											children: [
												oo[t],
												" · ",
												t
											]
										})]
									}),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-[10px] font-extrabold tracking-wider uppercase rounded-md bg-violet-100 text-violet-800 border border-violet-300 px-1.5 py-0.5",
										children: "Xem trước"
									})
								]
							}), E && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "absolute right-0 top-[52px] w-[260px] bg-white rounded-2xl border shadow-2xl p-2 z-50 anim-slide-up",
								role: "menu",
								"data-testid": "role-preview-menu",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "px-3 pt-2 pb-1 text-[12px] font-bold uppercase tracking-wide text-slate-400",
									children: "Xem trước giao diện theo vai trò — chỉ thay hiển thị, quyền thật theo tài khoản đăng nhập"
								}), [
									"ADMIN",
									"SUPPORT",
									"SALE"
								].map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
									role: "menuitem",
									onClick: () => {
										n(e), D(!1), g(`Đang XEM TRƯỚC giao diện ${oo[e]}`, "Chỉ thay đổi hiển thị trong sandbox — quyền thật vẫn theo tài khoản đăng nhập.", "blue");
									},
									className: U("w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between hover:bg-slate-50", t === e && "bg-blue-50"),
									children: [/* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsx)("span", {
										className: "block font-bold text-[14.5px]",
										children: oo[e]
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[12px] text-slate-500",
										children: e
									})] }), t === e && /* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-blue-700 font-bold text-[13px]",
										children: "● Đang xem"
									})]
								}, e))]
							})]
						}) : /* @__PURE__ */ (0, R.jsx)("div", {
							className: "hidden sm:block",
							"data-testid": "actual-role-badge",
							title: "Vai trò của tài khoản đăng nhập",
							children: /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 rounded-xl border-2 border-transparent pl-1.5 pr-2.5 py-1",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: U("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", t === "ADMIN" ? "bg-violet-600" : t === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600"),
									children: r.charAt(0)
								}), /* @__PURE__ */ (0, R.jsxs)("span", {
									className: "text-left leading-tight",
									children: [/* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[13px] font-bold text-[#0f2a4a]",
										children: r
									}), /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block text-[11.5px] text-slate-500",
										children: [
											oo[t],
											" · ",
											t
										]
									})]
								})]
							})
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => d(!0),
							className: "relative touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
							"aria-label": "Thông báo",
							children: [/* @__PURE__ */ (0, R.jsx)(Or, {
								size: 21,
								className: "text-[#0f2a4a]"
							}), S > 0 && /* @__PURE__ */ (0, R.jsx)("span", {
								className: "absolute top-1 right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-600 text-white text-[11px] font-extrabold grid place-items-center",
								children: S
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => p(!0),
							className: "hidden md:inline-flex touch-target items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px] hover:bg-[#14365e]",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }), " Thêm"]
						})
					]
				}), o && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "md:hidden px-3 pb-3 anim-slide-up",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center rounded-xl border-2 border-[#1e5aa8] bg-slate-50",
						children: [
							/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 18,
								className: "ml-3 text-slate-400"
							}),
							/* @__PURE__ */ (0, R.jsx)("input", {
								autoFocus: !0,
								value: i,
								onChange: (e) => a(e.target.value),
								placeholder: "Tìm mã lô · khách · hợp đồng…",
								className: "w-full bg-transparent px-2.5 py-3 text-[15px] outline-none"
							}),
							/* @__PURE__ */ (0, R.jsx)("button", {
								onClick: () => {
									s(!1), a("");
								},
								className: "mr-1 w-10 h-10 grid place-items-center",
								children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 18 })
							})
						]
					}), O && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-2 bg-white rounded-2xl border shadow-xl divide-y max-h-[50vh] overflow-auto",
						children: [
							O.lots.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => k(`/lo-hang/${e.id}`),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, R.jsx)(ra, {
									size: 18,
									className: "text-blue-700 shrink-0"
								}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "block font-bold text-[15px]",
									children: [
										e.id,
										" · ",
										e.customer
									]
								}), /* @__PURE__ */ (0, R.jsxs)("span", {
									className: "block text-[13px] text-slate-500",
									children: [
										e.status,
										" — ",
										e.nextAction
									]
								})] })]
							}, e.id)),
							O.cts.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => k(Yn(e.id)),
								className: "w-full text-left p-3.5 flex items-center gap-3",
								children: [/* @__PURE__ */ (0, R.jsx)(wi, {
									size: 18,
									className: "text-emerald-700 shrink-0"
								}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "block font-bold text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsxs)("span", {
									className: "block text-[13px] text-slate-500",
									children: [
										e.company,
										" — ",
										e.status
									]
								})] })]
							}, e.id)),
							O.lots.length + O.cts.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "p-4 text-[14px] text-slate-500",
								children: "Không tìm thấy. Thử lại theo mã lô, tên khách hàng hoặc số hợp đồng."
							})
						]
					})]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex flex-1 max-w-[1600px] w-full mx-auto",
				children: [
					/* @__PURE__ */ (0, R.jsx)("aside", {
						className: "no-print hidden lg:block w-[264px] shrink-0 border-r border-slate-200 bg-white min-h-[calc(100vh-64px)] sticky top-[64px] self-start max-h-[calc(100vh-64px)] overflow-y-auto",
						children: /* @__PURE__ */ (0, R.jsxs)("nav", {
							className: "p-3 pb-10",
							children: [so.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mb-4",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "px-3 mb-1.5 text-[11.5px] font-extrabold tracking-wider text-slate-400",
									children: e.group
								}), e.items.map((e) => {
									let t = So[e.icon] ?? ra;
									return /* @__PURE__ */ (0, R.jsxs)(Nn, {
										to: e.to,
										className: ({ isActive: t }) => U("flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14.5px] font-medium mb-0.5 transition-colors", t || e.to !== "/" && T.pathname.startsWith(e.to) ? "bg-[#0f2a4a] text-white shadow-md" : "text-slate-700 hover:bg-slate-100"),
										children: [
											/* @__PURE__ */ (0, R.jsx)(t, {
												size: 19,
												className: "shrink-0"
											}),
											/* @__PURE__ */ (0, R.jsx)("span", {
												className: "flex-1",
												children: e.label
											}),
											e.to === "/viec-can-xu-ly" && C > 0 && /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
												children: C
											}),
											e.soon && /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-[10.5px] font-extrabold uppercase tracking-wide rounded-full border border-slate-300 bg-slate-100 text-slate-500 px-2 py-0.5",
												children: "Sắp có"
											})
										]
									}, e.to);
								})]
							}, e.group)), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mx-1 mt-2 rounded-2xl bg-gradient-to-br from-[#0f2a4a] to-[#1e5aa8] text-white p-4",
								children: [
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-bold text-[14px]",
										children: "Cần hỗ trợ thao tác?"
									}),
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] text-blue-100 mt-1",
										children: "Sổ tay tra cứu quy trình, chứng từ và phân quyền cho Sale & Support."
									}),
									/* @__PURE__ */ (0, R.jsxs)(L, {
										to: "/so-tay",
										className: "mt-2.5 inline-flex items-center gap-1.5 bg-white text-[#0f2a4a] text-[13.5px] font-bold rounded-lg px-3 py-2",
										children: ["Mở sổ tay ", /* @__PURE__ */ (0, R.jsx)(Hr, { size: 15 })]
									})
								]
							})]
						})
					}),
					c && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "no-print fixed inset-0 z-50 lg:hidden",
						children: [/* @__PURE__ */ (0, R.jsx)("div", {
							className: "absolute inset-0 bg-slate-900/50 anim-fade",
							onClick: () => l(!1)
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "absolute left-0 top-0 bottom-0 w-[300px] max-w-[85vw] bg-white shadow-2xl overflow-y-auto anim-slide-up",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center justify-between p-4 border-b sticky top-0 bg-white z-10",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[#0f2a4a]",
									children: "Menu điều hành"
								}), /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => l(!1),
									className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
									children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 20 })
								})]
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "p-3",
								children: [
									b?.isSandbox && /* @__PURE__ */ (0, R.jsx)("div", {
										className: "flex gap-2 mb-3",
										"data-testid": "role-preview-mobile",
										children: [
											"ADMIN",
											"SUPPORT",
											"SALE"
										].map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
											onClick: () => {
												n(e), g(`Đang XEM TRƯỚC giao diện ${oo[e]}`, "Chỉ thay đổi hiển thị trong sandbox.", "blue");
											},
											className: U("flex-1 touch-target rounded-xl border-2 text-[13px] font-bold py-2", t === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600"),
											children: e
										}, e))
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "px-2 text-[12px] text-slate-500 mb-2",
										children: [
											"Đang dùng: ",
											/* @__PURE__ */ (0, R.jsx)("b", { children: r }),
											" · ",
											oo[t],
											b?.isSandbox ? " (xem trước giao diện)" : ""
										]
									}),
									so.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "mb-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "px-2 mb-1 text-[11px] font-extrabold tracking-wider text-slate-400",
											children: e.group
										}), e.items.map((e) => {
											let t = So[e.icon] ?? ra, n = e.to === "/" ? T.pathname === "/" : T.pathname.startsWith(e.to);
											return /* @__PURE__ */ (0, R.jsxs)(Nn, {
												to: e.to,
												onClick: () => l(!1),
												className: U("flex items-center gap-3 px-3 py-3 rounded-xl text-[15px] font-medium mb-0.5", n ? "bg-[#0f2a4a] text-white" : "text-slate-700 hover:bg-slate-100"),
												children: [
													/* @__PURE__ */ (0, R.jsx)(t, {
														size: 20,
														className: "shrink-0"
													}),
													e.label,
													e.to === "/viec-can-xu-ly" && C > 0 && /* @__PURE__ */ (0, R.jsx)("span", {
														className: "ml-auto text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1",
														children: C
													}),
													e.soon && /* @__PURE__ */ (0, R.jsx)("span", {
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
					/* @__PURE__ */ (0, R.jsxs)("main", {
						className: "flex-1 min-w-0 px-3 md:px-6 py-4 md:py-6 pb-28 md:pb-10 w-full",
						children: [e, /* @__PURE__ */ (0, R.jsxs)("footer", {
							className: "mt-10 text-center text-[12.5px] text-slate-400 pb-4",
							children: ["CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam · ", b?.isSandbox ? "Bản nội bộ — môi trường staging cách ly, mọi ghi nhận đi qua writer/RBAC/audit thật" : "Bản nội bộ — dữ liệu thật từ hệ thống Logistics, cập nhật liên tục"]
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsx)("nav", {
				className: "no-print md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,.08)]",
				style: { paddingBottom: "env(safe-area-inset-bottom)" },
				children: /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid grid-cols-5",
					children: [[
						{
							to: "/",
							label: "Tổng quan",
							icon: So.layout
						},
						{
							to: "/lo-hang",
							label: "Lô hàng",
							icon: ra
						},
						{
							to: "/hop-dong",
							label: "Hợp đồng",
							icon: wi
						},
						{
							to: "/tai-chinh/thu-tien",
							label: "Tài chính",
							icon: ro
						}
					].map((e) => {
						let t = e.to === "/" ? T.pathname === "/" : T.pathname.startsWith(e.to), n = e.icon;
						return /* @__PURE__ */ (0, R.jsxs)(Nn, {
							to: e.to,
							className: U("touch-target flex flex-col items-center justify-center gap-0.5 py-2 text-[11.5px] font-semibold", t ? "text-[#0f2a4a]" : "text-slate-400"),
							children: [
								/* @__PURE__ */ (0, R.jsx)(n, {
									size: 22,
									strokeWidth: t ? 2.4 : 1.8
								}),
								e.label,
								t && /* @__PURE__ */ (0, R.jsx)("span", { className: "w-8 h-1 rounded-full bg-[#0f2a4a]" })
							]
						}, e.to);
					}), /* @__PURE__ */ (0, R.jsxs)("button", {
						onClick: () => p(!0),
						className: "touch-target flex flex-col items-center justify-center gap-0.5 py-1.5 text-[11.5px] font-semibold text-slate-500",
						children: [/* @__PURE__ */ (0, R.jsx)("span", {
							className: "w-11 h-8 -mt-3 rounded-2xl bg-[#0f2a4a] text-white grid place-items-center shadow-lg",
							children: /* @__PURE__ */ (0, R.jsx)(ha, { size: 22 })
						}), "Thêm"]
					})]
				})
			}),
			u && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "no-print fixed inset-0 z-50",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/50 anim-fade",
					onClick: () => d(!1)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "absolute right-0 top-0 bottom-0 w-[380px] max-w-[92vw] bg-white shadow-2xl flex flex-col anim-slide-up",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center justify-between p-4 border-b",
							children: [/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-extrabold text-[16px] text-[#0f2a4a]",
								children: [
									"Thông báo · ",
									S,
									" chưa đọc"
								]
							}), /* @__PURE__ */ (0, R.jsx)("button", {
								onClick: () => d(!1),
								className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
								children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 20 })
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex-1 overflow-y-auto p-3 space-y-2",
							children: [x.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[14px] text-slate-500 p-4 text-center",
								children: "Không có cảnh báo nào theo dữ liệu hiện tại."
							}), x.map((e) => /* @__PURE__ */ (0, R.jsx)("div", {
								className: "rounded-2xl border border-slate-200 p-3.5 lift",
								children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex items-start gap-2.5",
									children: [/* @__PURE__ */ (0, R.jsx)("span", { className: U("w-2.5 h-2.5 rounded-full mt-1.5 shrink-0", e.tone === "red" ? "bg-red-500 pulse-dot" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500") }), /* @__PURE__ */ (0, R.jsxs)("div", { children: [
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-bold text-[14.5px] text-[#0f2a4a]",
											children: e.title
										}),
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[13.5px] text-slate-600 mt-0.5",
											children: e.desc
										}),
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-slate-400 mt-1",
											children: e.time
										})
									] })]
								})
							}, e.id))]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "p-3 border-t",
							children: /* @__PURE__ */ (0, R.jsx)("button", {
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
			f && /* @__PURE__ */ (0, R.jsx)(ko, {
				id: "quick-add-sheet",
				testId: "quick-add-sheet",
				labelledBy: "quick-add-title",
				width: 520,
				onClose: () => p(!1),
				children: /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "no-print",
					children: [
						/* @__PURE__ */ (0, R.jsx)("div", { className: "w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-4 sm:hidden" }),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center justify-between mb-1",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								id: "quick-add-title",
								className: "font-extrabold text-[18px] text-[#0f2a4a]",
								children: "Thêm mới nhanh"
							}), /* @__PURE__ */ (0, R.jsx)("button", {
								onClick: () => p(!1),
								"aria-label": "Đóng thêm mới nhanh",
								className: "touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100",
								children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 20 })
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500 mb-4",
							children: "Chọn việc muốn làm — mỗi nút dẫn thẳng tới màn hình nhập liệu."
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-2.5",
							children: [
								{
									label: "Tạo lô hàng mới",
									desc: "Từ báo giá đã chốt hoặc nhập tay",
									to: "/tao-lo-moi",
									icon: ra,
									bg: "bg-blue-50 text-blue-700"
								},
								{
									label: "Tạo hợp đồng mới",
									desc: "HDMB / HDNT + phụ lục",
									to: "/hop-dong/moi",
									icon: wi,
									bg: "bg-emerald-50 text-emerald-700"
								},
								{
									label: "Tạo báo giá",
									desc: "Dự toán chi phí & giá bán",
									to: "/kinh-doanh-bao-gia",
									icon: Pr,
									bg: "bg-violet-50 text-violet-700"
								},
								{
									label: "Ghi nhận thanh toán",
									desc: "Thu tiền khách / trả đối tác",
									to: "/tai-chinh/thu-tien",
									icon: ro,
									bg: "bg-amber-50 text-amber-700"
								},
								{
									label: "Tra cứu thuế / HS",
									desc: "Mã HS & mô tả hàng hóa",
									to: "/tra-cuu-thue",
									icon: qa,
									bg: "bg-slate-100 text-slate-700"
								}
							].map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => {
									p(!1), w(e.to);
								},
								className: "touch-target flex items-center gap-3 rounded-2xl border-2 border-slate-100 hover:border-[#1e5aa8] p-3.5 text-left lift bg-white",
								children: [
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: U("w-11 h-11 rounded-xl grid place-items-center shrink-0", e.bg),
										children: /* @__PURE__ */ (0, R.jsx)(e.icon, { size: 21 })
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "flex-1",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[15px] text-[#0f2a4a] flex items-center gap-2",
											children: e.label
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "block text-[13px] text-slate-500",
											children: e.desc
										})]
									}),
									/* @__PURE__ */ (0, R.jsx)(Hr, {
										size: 19,
										className: "text-slate-300"
									})
								]
							}, e.label))
						})
					]
				})
			}),
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "no-print fixed z-[60] left-3 right-3 bottom-[84px] md:left-auto md:right-6 md:bottom-6 md:w-[380px] space-y-2",
				children: m.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "toast-in rounded-2xl bg-[#0f2a4a] text-white p-4 shadow-2xl flex items-start gap-3",
					children: [
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: U("w-9 h-9 rounded-xl grid place-items-center shrink-0", e.tone === "green" ? "bg-emerald-500" : e.tone === "red" ? "bg-red-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500"),
							children: e.tone === "green" ? "✓" : e.tone === "red" ? "!" : e.tone === "amber" ? "⚠" : "i"
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex-1 min-w-0",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-bold text-[14.5px]",
								children: e.title
							}), e.desc && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] text-blue-100 mt-0.5",
								children: e.desc
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => h(e.id),
							className: "w-8 h-8 grid place-items-center rounded-lg hover:bg-white/10 shrink-0",
							children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 16 })
						})
					]
				}, e.id))
			}),
			o && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "fixed inset-0 z-30 hidden md:block",
				onClick: () => s(!1)
			})
		]
	});
}
//#endregion
//#region src/pages/Home.tsx
var Fo = {
	"Lô đang chạy": {
		icon: qa,
		bar: "bg-slate-500"
	},
	"Chờ lấy hàng": {
		icon: ta,
		bar: "bg-slate-500"
	},
	"Đang vận chuyển": {
		icon: qa,
		bar: "bg-blue-500"
	},
	"Chờ thông quan": {
		icon: gi,
		bar: "bg-amber-500"
	},
	"Chờ giao": {
		icon: ta,
		bar: "bg-blue-500"
	},
	"Đã giao": {
		icon: gi,
		bar: "bg-emerald-500"
	}
}, Io = {
	icon: bi,
	bar: "bg-red-500"
};
function Lo() {
	let { shipments: e, home: t, tasks: n, environment: r } = Jn(), i = yt(), a = t?.tiles ?? [], o = t?.focus ?? null, s = t?.summary, c = (n ?? []).slice(0, 3), l = t?.runningSummary ?? [], u = (/* @__PURE__ */ new Date()).toLocaleDateString("vi-VN", {
		weekday: "long",
		day: "2-digit",
		month: "2-digit",
		year: "numeric"
	}), d = (s?.critical ?? 0) + (t?.urgentCount ?? 0);
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1200px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8] text-white p-4 md:p-5",
				children: [/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[12.5px] font-semibold text-blue-200 uppercase tracking-wider",
					children: [u, r?.isSandbox ? ` · ${r.label}` : ""]
				}), o ? /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
					/* @__PURE__ */ (0, R.jsxs)("h1", {
						className: "text-[19px] md:text-[23px] font-extrabold leading-snug mt-1",
						children: ["Ưu tiên bây giờ: ", /* @__PURE__ */ (0, R.jsxs)("span", {
							className: "text-white",
							children: [
								o.id,
								" — ",
								o.nextAction
							]
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] md:text-[14.5px] text-blue-100 mt-1 max-w-[760px]",
						children: [
							t?.urgentCount ?? 0,
							" việc khẩn · ",
							K(o.nextActionDetail)
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap gap-2.5 mt-3.5",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => i(o.to),
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]",
								children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 18 })]
							}),
							/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => i(`/lo-hang/${o.id}`),
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]",
								children: ["Mở ", o.id]
							}),
							/* @__PURE__ */ (0, R.jsx)(L, {
								to: "/viec-can-xu-ly",
								className: "btn-press touch-target inline-flex items-center rounded-xl text-white/90 font-bold text-[14px] px-4 min-h-[48px] underline decoration-white/40 underline-offset-4",
								children: "Xem cả danh sách việc"
							})
						]
					})
				] }) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)("h1", {
					className: "text-[19px] md:text-[23px] font-extrabold leading-snug mt-1",
					children: "Không có việc khẩn — toàn bộ lô hàng đang ổn định."
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "flex flex-wrap gap-2.5 mt-3.5",
					children: /* @__PURE__ */ (0, R.jsxs)(L, {
						to: "/lo-hang",
						className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]",
						children: ["Mở danh sách lô ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 18 })]
					})
				})] })]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center justify-between mb-2.5",
						children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[16px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(ei, {
								size: 18,
								className: "text-red-600"
							}), " Quá hạn và sắp tới hạn"]
						}), /* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/viec-can-xu-ly",
							className: "text-[13px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
							children: ["Tất cả ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 14 })]
						})]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "space-y-2",
						children: [c.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 py-2",
							children: "Không có việc tới hạn theo readiness hiện tại."
						}), c.map((e) => /* @__PURE__ */ (0, R.jsxs)(L, {
							to: e.route,
							className: "flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-2.5 lift",
							children: [
								/* @__PURE__ */ (0, R.jsx)("span", { className: U("w-2.5 h-9 rounded-full shrink-0", e.statusTone === "red" ? "bg-red-500" : e.statusTone === "amber" ? "bg-amber-500" : e.statusTone === "blue" ? "bg-blue-500" : "bg-slate-400") }),
								/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "flex-1 min-w-0",
									children: [/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block font-bold text-[14px] text-[#0f2a4a]",
										children: [
											e.lot,
											" · ",
											e.job
										]
									}), /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block text-[12.5px] text-slate-500",
										children: [
											K(e.due),
											" · ",
											K(e.dueNote)
										]
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "touch-target inline-flex items-center text-[13px] font-bold text-[#1e5aa8]",
									children: ["Xử lý ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 14 })]
								})
							]
						}, e.id))]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center justify-between mb-2.5",
						children: [/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[16px] text-[#0f2a4a]",
							children: "Trạng thái các lô đang chạy"
						}), /* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/lo-hang",
							className: "text-[13px] font-bold text-[#1e5aa8] inline-flex items-center gap-1",
							children: ["Tất cả lô ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 14 })]
						})]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "space-y-2",
						children: [l.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 py-2",
							children: "Không có lô nào đang chạy."
						}), l.map((t) => {
							let n = e.find((e) => e.id === t.id);
							return /* @__PURE__ */ (0, R.jsxs)(L, {
								to: t.to,
								className: "flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-2.5 lift",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Co, { tone: n?.statusTone ?? "gray" }),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "flex-1 min-w-0",
										children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14px] text-[#0f2a4a]",
											children: [
												t.id,
												" · ",
												t.customer
											]
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500 truncate",
											children: ["Tiếp theo: ", t.nextAction]
										})]
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: n?.statusTone ?? "gray",
										size: "sm",
										children: t.status
									})
								]
							}, t.id);
						})]
					})]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", { children: [/* @__PURE__ */ (0, R.jsx)(J, {
				title: "Ảnh vận hành hôm nay",
				sub: "Số liệu thật từ Logistics — bấm một ô để mở đúng danh sách lô"
			}), /* @__PURE__ */ (0, R.jsx)("div", {
				className: "grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2.5",
				"data-testid": "home-snapshot",
				children: a.map((e) => {
					let t = Fo[e.label] ?? Io, n = t.icon;
					return /* @__PURE__ */ (0, R.jsxs)(L, {
						to: e.to,
						className: "lift btn-press rounded-2xl bg-white border border-slate-200 p-3 flex flex-col gap-1.5",
						title: e.sub,
						children: [
							/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "flex items-center gap-1.5 text-[12.5px] font-semibold text-slate-500 truncate",
								children: [
									/* @__PURE__ */ (0, R.jsx)("span", { className: U("w-1.5 h-4 rounded-full shrink-0", t.bar) }),
									/* @__PURE__ */ (0, R.jsx)(n, {
										size: 15,
										className: "shrink-0 text-slate-400"
									}),
									e.label
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "tnum text-[22px] md:text-[24px] font-extrabold text-[#0f2a4a] leading-none",
								children: e.value
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-[12px] text-slate-400 leading-snug line-clamp-2 min-h-[2em]",
								children: e.sub
							})
						]
					}, e.label);
				})
			})] }),
			/* @__PURE__ */ (0, R.jsxs)("section", { children: [/* @__PURE__ */ (0, R.jsx)(J, {
				title: "Tiền & hồ sơ cần chú ý",
				sub: "Hiện trạng → việc thiếu → bấm để xử lý ngay"
			}), /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3.5 flex flex-col",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] font-semibold text-emerald-800 flex items-center gap-1.5",
								children: [
									/* @__PURE__ */ (0, R.jsx)(ro, { size: 15 }),
									" Còn phải thu · ",
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "tnum font-extrabold",
										children: [vo(t?.outstandingTotal), " ₫"]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-emerald-900 mt-1 flex-1",
								children: [t?.outstandingCount ?? 0, " lô còn công nợ theo core.logic"]
							}),
							/* @__PURE__ */ (0, R.jsx)(L, {
								to: "/tai-chinh/thu-tien",
								className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-[14px] px-4 min-h-[44px]",
								children: "GHI NHẬN THANH TOÁN"
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl bg-amber-50 border border-amber-200 p-3.5 flex flex-col",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] font-semibold text-amber-800 flex items-center gap-1.5",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ca, { size: 15 }),
									" Cần đối soát · ",
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "tnum font-extrabold",
										children: [s?.financialAttention ?? 0, " lô"]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] text-amber-900 mt-1 flex-1",
								children: "Quote Estimate ≠ Finance Actual — đối soát từng lô"
							}),
							/* @__PURE__ */ (0, R.jsx)(L, {
								to: "/tai-chinh/doi-soat",
								className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-amber-500 text-white font-bold text-[14px] px-4 min-h-[44px]",
								children: "ĐỐI SOÁT NGAY"
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl bg-blue-50 border border-blue-200 p-3.5 flex flex-col",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] font-semibold text-blue-800 flex items-center gap-1.5",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ei, { size: 15 }),
									" Hồ sơ thiếu thông tin · ",
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "tnum font-extrabold",
										children: t?.missingDocsTotal ?? 0
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-blue-900 mt-1 flex-1",
								children: [s?.missingInfo ?? 0, " lô thiếu dữ liệu bắt buộc"]
							}),
							/* @__PURE__ */ (0, R.jsx)(L, {
								to: "/viec-can-xu-ly",
								className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[44px]",
								children: "MỞ DANH SÁCH VIỆC"
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl bg-red-50 border border-red-200 p-3.5 flex flex-col",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] font-semibold text-red-800 flex items-center gap-1.5",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Vi, { size: 15 }),
									" Việc quá hạn / khẩn · ",
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "tnum font-extrabold",
										children: [d, " việc"]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-red-900 mt-1 flex-1",
								children: [s?.deadlineSoon ?? 0, " lô sắp tới hạn khách"]
							}),
							/* @__PURE__ */ (0, R.jsx)(L, {
								to: "/viec-can-xu-ly",
								className: "btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-red-600 text-white font-bold text-[14px] px-4 min-h-[44px]",
								children: "XỬ LÝ VIỆC KHẨN"
							})
						]
					})
				]
			})] })
		]
	});
}
//#endregion
//#region src/lib/queryParam.ts
function Ro(e) {
	let [t, n] = Rn();
	return [t.get(e) ?? "", (0, _.useCallback)((t) => {
		n((n) => {
			let r = new URLSearchParams(n);
			return t ? r.set(e, t) : r.delete(e), r;
		}, { replace: !0 });
	}, [n, e])];
}
function zo(e) {
	let [t, n] = Rn();
	return [t.get(e) === "1", (0, _.useCallback)((t) => {
		n((n) => {
			let r = new URLSearchParams(n);
			return t ? r.set(e, "1") : r.delete(e), r;
		}, { replace: !0 });
	}, [n, e])];
}
//#endregion
//#region src/pages/Tasks.tsx
var Bo = {
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
function Vo() {
	let [e, t] = Ro("level"), n = e || "ALL", r = (e) => t(e === "ALL" ? "" : e), [i, a] = Ro("q"), o = (0, _.useMemo)(() => po.filter((e) => (n === "ALL" || e.level === n) && (!i || (e.lot + e.customer + e.job + e.assignee).toLowerCase().includes(i.toLowerCase()))), [n, i]), s = (0, _.useMemo)(() => ({
		ALL: po.length,
		Khan: po.filter((e) => e.level === "Khan").length,
		CanXuLy: po.filter((e) => e.level === "CanXuLy").length,
		BinhThuong: po.filter((e) => e.level === "BinhThuong").length
	}), [po.length, po]);
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					title: "Việc Cần Xử Lý",
					sub: "Hiện trạng → việc thiếu → bấm XỬ LÝ NGAY để tới đúng ô cần nhập. Làm mục Khẩn trước 17:00."
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "flex flex-col md:flex-row gap-2.5",
					children: [/* @__PURE__ */ (0, R.jsx)("input", {
						value: i,
						onChange: (e) => a(e.target.value),
						placeholder: "Lọc theo mã lô, khách hàng, người phụ trách…",
						className: "flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none"
					}), /* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2 overflow-x-auto no-scrollbar",
						children: [
							"ALL",
							"Khan",
							"CanXuLy",
							"BinhThuong"
						].map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => r(e),
							className: U("touch-target shrink-0 rounded-xl border-2 px-4 min-h-[48px] text-[14.5px] font-bold", n === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? `Tất cả (${s.ALL})` : e === "Khan" ? `Khẩn (${s.Khan})` : e === "CanXuLy" ? `Cần xử lý (${s.CanXuLy})` : `Bình thường (${s.BinhThuong})`
						}, e))
					})]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14.5px] min-w-[980px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Ưu tiên" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã lô" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Việc cần làm" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Người phụ trách" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hạn" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: o.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("span", {
									className: U("inline-flex items-center gap-1.5 text-[12.5px] font-extrabold rounded-full px-2.5 py-1 whitespace-nowrap", Bo[e.level].cls),
									children: Bo[e.level].label
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-extrabold text-[#0f2a4a]",
									children: /* @__PURE__ */ (0, R.jsx)(L, {
										to: e.route,
										className: "hover:underline whitespace-nowrap",
										children: e.lot
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: e.customer }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "max-w-[260px]",
									children: /* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-semibold",
										children: e.job
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "whitespace-nowrap",
									children: e.assignee
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", { children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-bold text-red-700 whitespace-nowrap",
									children: e.due
								}), /* @__PURE__ */ (0, R.jsx)("span", {
									className: "block text-[12.5px] text-slate-500",
									children: e.dueNote
								})] }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)(L, {
									to: e.route,
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white text-[13.5px] font-bold px-3.5 min-h-[44px] whitespace-nowrap",
									children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 15 })]
								}) })
							]
						}, e.id)) })]
					})
				}), o.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "p-8 text-center text-slate-500",
					children: ["Không có việc nào khớp. ", /* @__PURE__ */ (0, R.jsx)("button", {
						onClick: () => {
							r("ALL"), a("");
						},
						className: "font-bold text-[#1e5aa8]",
						children: "Xóa lọc"
					})]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [o.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center gap-2 flex-wrap",
							children: [
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: U("inline-flex items-center text-[12px] font-extrabold rounded-full px-2.5 py-1", Bo[e.level].cls),
									children: Bo[e.level].label
								}),
								/* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}),
								/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "ml-auto text-[12.5px] font-bold text-red-700",
									children: ["⏰ ", e.due]
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "font-extrabold text-[16px] text-[#0f2a4a] mt-2",
							children: [
								e.lot,
								" · ",
								e.customer
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-1.5 rounded-xl bg-slate-50 border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
									children: "Việc cần làm"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[15px] font-semibold text-slate-800 mt-0.5",
									children: e.job
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
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
						/* @__PURE__ */ (0, R.jsxs)(L, {
							to: e.route,
							className: "btn-press touch-target mt-3 flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[15.5px] min-h-[52px]",
							children: ["XỬ LÝ NGAY ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 18 })]
						})
					]
				}, e.id)), o.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center text-slate-500",
					children: ["Không có việc nào. ", /* @__PURE__ */ (0, R.jsx)("button", {
						onClick: () => {
							r("ALL"), a("");
						},
						className: "font-bold text-[#1e5aa8]",
						children: "Xóa lọc"
					})]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-4 flex items-start gap-3 text-[14px] text-slate-500",
				children: [/* @__PURE__ */ (0, R.jsx)(zi, {
					size: 19,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, R.jsxs)("p", { children: [
					"Mẹo cho người mới: xử lý theo thứ tự ",
					/* @__PURE__ */ (0, R.jsx)("b", { children: "Khẩn → Cần xử lý → Bình thường" }),
					". Mỗi dòng đều có nút XỬ LÝ NGAY dẫn tới đúng ô nhập liệu."
				] })]
			})
		]
	});
}
//#endregion
//#region src/components/GetFlyImport.tsx
var Ho = "SHIPMENT_ONLY", Uo = "SHIPMENT_AND_FINANCE", Wo = 10485760;
function Go(e) {
	return `${e}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}
function Ko(e) {
	return e === "CREATED" ? "CREATED" : e === "SKIPPED_ALREADY_EXISTS" ? "SKIPPED_ALREADY_EXISTS" : e === "REFUSED_VALIDATION" ? "REFUSED_VALIDATION" : "FAILED_WRITE";
}
function qo(e) {
	return !e.existing;
}
function Jo() {
	let { dispatch: e, toast: t } = Jn(), n = (0, _.useSyncExternalStore)(C, S, S), r = n?.getfly ?? {
		status: "EMPTY",
		previewId: "",
		filename: "",
		orders: [],
		summary: {
			orders: 0,
			revenue: null,
			profit: null
		},
		error: ""
	}, i = n?.lastWrites ?? [], a = (0, _.useRef)(null), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)(""), [u, d] = (0, _.useState)(Ho), [f, p] = (0, _.useState)({}), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)([]), [x, w] = (0, _.useState)("");
	(0, _.useEffect)(() => {
		if (!o) return;
		let e = i.find((e) => e.event === "getfly_preview" && e.requestId === o);
		e && (s(""), e.ok ? (v(""), h("")) : v(String(e.error || "Không đọc được DSDH.xlsx.")));
	}, [i, o]), (0, _.useEffect)(() => {
		if (!c) return;
		let e = i.find((e) => e.event === "getfly_import" && e.requestId === c);
		if (!e) return;
		l("");
		let n = Array.isArray(e.results) ? e.results.filter((e) => !!(e && typeof e == "object")) : [];
		b(n), e.ok ? (v(""), h(""), t("GetFly đã được ghi nhận", "Đã đọc lại dữ liệu mới từ backend.", "green")) : v(String(e.error || "Nhập GetFly bị từ chối."));
	}, [
		i,
		c,
		t
	]), (0, _.useEffect)(() => {
		r.previewId && r.previewId !== x && (w(r.previewId), p({}), b([]), h(""), v(""));
	}, [r.previewId, x]);
	let T = (0, _.useMemo)(() => r.orders.filter(qo), [r.orders]), E = (0, _.useMemo)(() => T.reduce((e, t) => e + t.serviceLines.length, 0), [T]), D = (0, _.useMemo)(() => {
		if (u !== Uo) return [];
		let e = [];
		for (let t of T) for (let n of t.serviceLines) {
			let r = f[n.lineId] ?? "";
			r.trim() ? (!Number.isFinite(Number(r)) || Number(r) < 0 || Number(r) > 100) && e.push(`${t.orderId} · ${n.lineId}: VAT không hợp lệ`) : e.push(`${t.orderId} · ${n.lineId}: VAT chưa nhập`), (n.qty == null || Number(n.qty) <= 0) && e.push(`${t.orderId} · ${n.lineId}: Số lượng UNKNOWN/không hợp lệ`), n.cost ?? e.push(`${t.orderId} · ${n.lineId}: Giá vốn UNKNOWN`), n.price ?? e.push(`${t.orderId} · ${n.lineId}: Giá bán UNKNOWN`), n.name.trim() || e.push(`${t.orderId} · ${n.lineId}: Tên dịch vụ UNKNOWN`);
		}
		return e;
	}, [
		u,
		T,
		f
	]), O = () => a.current?.click(), k = (t) => {
		let n = t.currentTarget.files?.[0];
		if (t.currentTarget.value = "", !n) return;
		if (b([]), h(""), v(""), !n.name.toLowerCase().endsWith(".xlsx")) {
			v("Chỉ nhận file DSDH.xlsx / .xlsx.");
			return;
		}
		if (n.size > Wo) {
			v(`File DSDH vượt giới hạn ${Wo / 1048576} MB.`);
			return;
		}
		let r = Go("GF-PREVIEW");
		s(r);
		let i = new FileReader();
		i.onerror = () => {
			s(""), v("Không đọc được bytes từ file đã chọn.");
		}, i.onload = () => {
			let t = typeof i.result == "string" ? i.result : "", a = t.indexOf(","), o = a >= 0 ? t.slice(a + 1) : t;
			if (!o) {
				s(""), v("File DSDH không có dữ liệu.");
				return;
			}
			e("getfly_preview", {
				filename: n.name,
				mime: n.type,
				size: n.size,
				contentBase64: o,
				requestId: r
			}) || (s(""), v("Không gửi được ý định xem trước tới backend."));
		}, i.readAsDataURL(n);
	}, A = (e, t) => {
		p((n) => ({
			...n,
			[e]: t
		})), h(""), v("");
	}, ee = () => {
		if (!r.previewId) {
			h("Chưa có preview hợp lệ. Hãy chọn DSDH.xlsx trước.");
			return;
		}
		if (u === Uo && D.length > 0) {
			h("Không thể xác nhận: mỗi dòng dịch vụ của lô mới phải có Giá vốn, Giá bán, Số lượng và VAT. VAT trống không phải là 0.");
			return;
		}
		let t = Go("GF-COMMIT"), n = {
			previewId: r.previewId,
			mode: u,
			requestId: t
		};
		if (u === Uo && (n.vatByLineId = f), !e("getfly_import", n)) {
			v("Không gửi được xác nhận nhập GetFly tới backend.");
			return;
		}
		l(t), v(""), h("");
	}, j = r.status === "READY" && !!r.previewId;
	return /* @__PURE__ */ (0, R.jsxs)("section", {
		className: "rounded-2xl bg-white border-2 border-sky-200 p-4 md:p-5 space-y-4",
		"data-testid": "getfly-import",
		children: [
			/* @__PURE__ */ (0, R.jsx)(J, {
				icon: /* @__PURE__ */ (0, R.jsx)(Si, { size: 19 }),
				title: "Nhập GetFly DSDH",
				sub: "DSDH.xlsx → xem trước trên server → xác nhận tạo các lô còn thiếu",
				right: /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)("input", {
					ref: a,
					type: "file",
					accept: ".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					onChange: k,
					className: "hidden",
					"data-testid": "getfly-file-input",
					"aria-label": "Chọn DSDH.xlsx"
				}), /* @__PURE__ */ (0, R.jsxs)("button", {
					type: "button",
					onClick: O,
					disabled: o !== "",
					className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-3.5 min-h-[46px] disabled:opacity-50",
					"data-testid": "getfly-choose-file",
					children: [o ? /* @__PURE__ */ (0, R.jsx)(Ui, {
						size: 17,
						className: "animate-spin"
					}) : /* @__PURE__ */ (0, R.jsx)(Ya, { size: 17 }), o ? "ĐANG ĐỌC…" : "NHẬP GETFLY DSDH"]
				})] })
			}),
			(m || g) && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-xl border-2 border-red-300 bg-red-50 p-3 text-[13.5px] text-red-800 flex items-start gap-2",
				"data-testid": "getfly-error",
				children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
					size: 17,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, R.jsx)("span", { children: m || g })]
			}),
			o && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-xl border border-sky-200 bg-sky-50 p-3 text-[14px] text-sky-900 flex items-center gap-2",
				"data-testid": "getfly-parsing",
				children: [/* @__PURE__ */ (0, R.jsx)(Ui, {
					size: 17,
					className: "animate-spin"
				}), " Đang gửi bytes tới backend để đọc DSDH.xlsx… Chưa có thao tác ghi dữ liệu."]
			}),
			!j && !o && !g && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-4 text-[14px] text-slate-600",
				"data-testid": "getfly-empty",
				children: "Chọn đúng file DSDH.xlsx để xem số đơn, doanh thu, lợi nhuận, dịch vụ và trạng thái đã có/chưa có. Chọn file chỉ tạo preview, chưa ghi lô hay Finance Actual."
			}),
			j && /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-xl border border-slate-200 bg-slate-50 p-3",
					"data-testid": "getfly-preview-meta",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap items-center gap-2 text-[13.5px]",
						children: [
							/* @__PURE__ */ (0, R.jsxs)(q, {
								tone: "blue",
								size: "sm",
								children: ["PREVIEW · ", r.filename]
							}),
							/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "text-slate-500",
								children: [
									r.orders.length,
									" đơn · previewId ",
									r.previewId
								]
							}),
							r.fingerprint && /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "text-slate-400 font-mono text-[11px]",
								children: [
									"SHA-256 ",
									r.fingerprint.slice(0, 16),
									"…"
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 sm:grid-cols-3 gap-2.5 mt-3",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-white border border-slate-200 p-3",
								"data-testid": "getfly-kpi-revenue",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-400",
									children: "Doanh Thu GF"
								}), /* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[20px] text-[#0f2a4a]",
									children: W(r.summary.revenue)
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-white border border-slate-200 p-3",
								"data-testid": "getfly-kpi-profit",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-400",
									children: "Lợi Nhuận GF"
								}), /* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[20px] text-emerald-700",
									children: W(r.summary.profit)
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-white border border-slate-200 p-3",
								"data-testid": "getfly-kpi-orders",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-400",
									children: "Số Đơn"
								}), /* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[20px] text-[#0f2a4a]",
									children: bo(r.summary.orders)
								})]
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, R.jsx)("div", {
					className: "space-y-3",
					"data-testid": "getfly-orders",
					children: r.orders.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border-2 border-slate-200 bg-white overflow-hidden",
						"data-testid": `getfly-order-${e.orderId}`,
						children: [/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "p-3.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-start justify-between gap-2",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", { children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[16px] text-[#0f2a4a]",
									children: e.orderId
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[13.5px] text-slate-700",
									children: [
										K(e.customer),
										" · Ngày: ",
										K(e.orderDate)
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] text-slate-500",
									children: [
										"Trạng thái nguồn: ",
										K(e.sourceStatus),
										" · Mã KH: ",
										K(e.customerCode)
									]
								})
							] }), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-1.5",
								children: [/* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.existing ? "green" : "amber",
									size: "sm",
									children: e.existing ? "Đã có trong hệ thống" : "Lô còn thiếu — sẽ tạo"
								}), /* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.customerMatch === "UNKNOWN" ? "amber" : "blue",
									size: "sm",
									children: e.customerMatch === "UNKNOWN" ? "Khách master: UNKNOWN" : `Khách master: ${e.customerMatch === "MATCHED_BY_CODE" ? "đúng mã" : "đúng tên"}`
								})]
							})]
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "p-3.5 overflow-x-auto",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center justify-between gap-2 mb-2",
								children: [/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "font-bold text-[14px] text-slate-700",
									children: [
										"Dịch vụ / sản phẩm (",
										e.serviceLines.length,
										" dòng)"
									]
								}), /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[13px] text-slate-500",
									children: [
										"Doanh thu: ",
										/* @__PURE__ */ (0, R.jsx)("b", { children: W(e.revenue) }),
										" · Lợi nhuận: ",
										/* @__PURE__ */ (0, R.jsx)("b", { children: W(e.profit) })
									]
								})]
							}), /* @__PURE__ */ (0, R.jsxs)("table", {
								className: "tbl w-full text-[12.5px] min-w-[840px]",
								children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Tên" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Mô tả" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "SL" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Giá vốn" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Giá bán" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Thành tiền" }),
									u === Uo && /* @__PURE__ */ (0, R.jsx)("th", { children: "VAT % *" })
								] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: e.serviceLines.map((t) => /* @__PURE__ */ (0, R.jsxs)("tr", {
									"data-testid": `getfly-line-${t.lineId}`,
									children: [
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-bold",
											children: K(t.code)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-semibold",
											children: K(t.name)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: K(t.description) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: bo(t.qty) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: W(t.cost) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: W(t.price) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: W(t.revenue) }),
										u === Uo && /* @__PURE__ */ (0, R.jsx)("td", { children: qo(e) ? /* @__PURE__ */ (0, R.jsx)("input", {
											value: f[t.lineId] ?? "",
											onChange: (e) => A(t.lineId, e.target.value),
											inputMode: "decimal",
											placeholder: "Nhập VAT",
											className: U(X(f[t.lineId]?.trim() ? "ok" : "missing"), "min-w-[115px]"),
											"data-testid": `getfly-vat-${t.lineId}`,
											"aria-label": `VAT ${e.orderId} ${t.lineId}`
										}) : /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-slate-400",
											children: "— bỏ qua"
										}) })
									]
								}, t.lineId)) })]
							})]
						})]
					}, e.orderId))
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-xl border-2 border-indigo-200 bg-indigo-50/60 p-3.5 space-y-3",
					"data-testid": "getfly-commit-panel",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-extrabold text-[15px] text-[#0f2a4a]",
							children: "Phạm vi nhập"
						}),
						/* @__PURE__ */ (0, R.jsxs)("label", {
							className: "flex items-start gap-2.5 rounded-xl border-2 border-white bg-white p-3 cursor-pointer",
							children: [/* @__PURE__ */ (0, R.jsx)("input", {
								type: "radio",
								name: "getfly-mode",
								value: Ho,
								checked: u === Ho,
								onChange: () => {
									d(Ho), h("");
								},
								"data-testid": "getfly-mode-shipment-only"
							}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsx)("b", { children: "CHỈ TẠO LÔ TỪ GETFLY" }), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "block text-[13px] text-slate-600",
								children: "Tạo lô thiếu theo mã đơn, khách, ngày, trạng thái. Không ghi giá vốn/giá bán/VAT vào Finance Actual."
							})] })]
						}),
						/* @__PURE__ */ (0, R.jsxs)("label", {
							className: "flex items-start gap-2.5 rounded-xl border-2 border-white bg-white p-3 cursor-pointer",
							children: [/* @__PURE__ */ (0, R.jsx)("input", {
								type: "radio",
								name: "getfly-mode",
								value: Uo,
								checked: u === Uo,
								onChange: () => {
									d(Uo), h("");
								},
								"data-testid": "getfly-mode-finance"
							}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [/* @__PURE__ */ (0, R.jsx)("b", { children: "TẠO LÔ + GHI DỊCH VỤ THỰC TẾ" }), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "block text-[13px] text-slate-600",
								children: "Mỗi lô mới phải có Giá vốn, Giá bán và VAT do operator nhập. VAT trống bị từ chối; VAT 0 là một câu trả lời hợp lệ."
							})] })]
						}),
						u === Uo && /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[13px] text-indigo-900",
							children: [
								"Đang chờ VAT cho ",
								E,
								" dòng dịch vụ của ",
								T.length,
								" lô mới. Các lô đã có sẽ được bỏ qua."
							]
						}),
						D.length > 0 && u === Uo && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-lg border border-amber-300 bg-amber-50 p-2.5 text-[13px] text-amber-900",
							"data-testid": "getfly-finance-warning",
							children: ["VAT / tiền bắt buộc chưa đủ — XÁC NHẬN sẽ bị chặn cho đến khi operator nhập đủ. Ví dụ: ", D[0]]
						}),
						y.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "space-y-2",
							"data-testid": "getfly-results",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-bold text-[14px]",
								children: "Kết quả authoritative từ backend"
							}), y.map((e, t) => {
								let n = String(e.status || "");
								return /* @__PURE__ */ (0, R.jsxs)("div", {
									className: U("rounded-lg border p-2.5 text-[13px]", n === "CREATED" || n === "SKIPPED_ALREADY_EXISTS" ? "border-emerald-300 bg-emerald-50 text-emerald-900" : "border-red-300 bg-red-50 text-red-900"),
									children: [
										/* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-extrabold",
											children: String(e.orderId || "UNKNOWN")
										}),
										" · ",
										Ko(n),
										" ",
										e.message ? `· ${String(e.message)}` : "",
										" ",
										e.error ? `· ${String(e.error)}` : "",
										" ",
										Array.isArray(e.errors) ? `· ${e.errors.join(" ")}` : "",
										n === "CREATED" && /* @__PURE__ */ (0, R.jsx)(Kr, {
											size: 15,
											className: "inline ml-1"
										})
									]
								}, `${String(e.orderId)}-${t}`);
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsxs)(wo, {
								onClick: ee,
								disabled: !!c || !j,
								children: [c ? /* @__PURE__ */ (0, R.jsx)(Ui, {
									size: 17,
									className: "animate-spin"
								}) : /* @__PURE__ */ (0, R.jsx)(Kr, { size: 17 }), c ? "ĐANG CHỜ BACKEND…" : "XÁC NHẬN NHẬP"]
							}), /* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => {
									d(Ho), b([]), h(""), v("");
								},
								children: "ĐỔI VỀ CHỈ TẠO LÔ"
							})]
						})
					]
				})
			] })
		]
	});
}
//#endregion
//#region src/pages/Shipments.tsx
function Yo() {
	let { shipments: e } = Jn(), [t, n] = Ro("q"), [r, i] = Ro("status"), a = r || "ALL", o = (e) => i(e === "ALL" ? "" : e), [s, c] = (0, _.useState)(() => r !== ""), l = (0, _.useMemo)(() => e.filter((e) => (a === "ALL" || e.status === a) && (!t || (e.id + e.customer + e.contract + e.route + e.sale + e.support).toLowerCase().includes(t.toLowerCase()))), [
		e,
		t,
		a
	]), u = ["ALL", ...Array.from(new Set(e.map((e) => e.status)))];
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsx)(Jo, {}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						title: "Lô Hàng",
						sub: "Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu",
						right: /* @__PURE__ */ (0, R.jsx)(L, {
							to: "/tao-lo-moi",
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: "＋ Tạo lô mới"
						})
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								placeholder: "Nhập mã lô (LO-0306), khách (An Phát), hợp đồng…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => c((e) => !e),
							className: U("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, R.jsx)(Fa, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					s && /* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: u.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => o(e),
							className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", a === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : e
						}, e))
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [l.length, " lô"]
							}),
							t ? /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
								" cho “",
								t,
								"”"
							] }) : null,
							" · Mỗi lô hiển thị: hiện trạng → việc tiếp theo → nút xử lý."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: /* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[1080px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã lô" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hợp đồng · Tuyến" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Việc tiếp theo" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Sale · Support" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: l.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("td", { children: [/* @__PURE__ */ (0, R.jsx)(L, {
									to: "/lo-hang/" + e.id,
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsxs)("span", {
									className: "block text-[12px] text-slate-400",
									children: ["Cập nhật ", e.updated]
								})] }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "max-w-[220px]",
									children: [/* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[13px] font-semibold text-slate-600",
										children: e.contract
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[13px] text-slate-500",
										children: e.route
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.statusTone,
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "max-w-[240px]",
									children: /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block font-semibold text-[13.5px]",
										children: e.nextAction
									})
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Sale: ", /* @__PURE__ */ (0, R.jsx)("b", { children: e.sale })]
									}), /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Cập nhật bởi: ", /* @__PURE__ */ (0, R.jsx)("b", { children: e.support || "—" })]
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, R.jsx)(L, {
										to: e.nextRoute,
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]",
										children: "XỬ LÝ"
									}), /* @__PURE__ */ (0, R.jsxs)(L, {
										to: "/lo-hang/" + e.id,
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }), " 360°"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [l.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Co, { tone: e.statusTone }),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: e.statusTone,
										size: "sm",
										children: e.status
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] text-slate-500",
								children: e.route
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-2.5 rounded-xl bg-amber-50 border border-amber-200 p-3",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[11.5px] font-bold uppercase tracking-wide text-amber-700",
									children: "Việc tiếp theo"
								}), /* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[14px] font-semibold text-slate-800 mt-0.5",
									children: e.nextAction
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-2",
								children: [
									"Sale ",
									e.sale,
									" · cập nhật bởi ",
									e.support || "—",
									" · ",
									e.updated
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, R.jsxs)(L, {
							to: e.nextRoute,
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: ["XỬ LÝ ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
						}), /* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/lo-hang/" + e.id,
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 17 }), " XEM 360°"]
						})]
					})]
				}, e.id)), l.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy lô nào"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo lô mới."
						}),
						/* @__PURE__ */ (0, R.jsx)(L, {
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
//#region src/components/ShipmentOperations.tsx
var Xo = [
	"Truck",
	"Sea",
	"Air",
	"Rail"
], Zo = (e) => `${e}-${typeof crypto < "u" && typeof crypto.randomUUID == "function" ? crypto.randomUUID() : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`}`, Qo = (e, t = "Truck") => ({
	id: Zo("leg"),
	sequence: e,
	mode: t,
	origin: "",
	destination: "",
	carrier: "",
	etd: "",
	eta: "",
	atd: "",
	ata: "",
	bookingNo: "",
	mbl: "",
	hbl: "",
	vessel: "",
	voyage: "",
	mawb: "",
	hawb: "",
	flightNo: "",
	units: []
}), $o = (e) => ({
	id: Zo(e),
	kind: e,
	number: "",
	typeSize: "",
	sealNo: "",
	driverName: "",
	driverPhone: ""
}), es = (e) => ({
	goodsDescription: e?.goodsDescription ?? "",
	packageCount: e?.packs == null ? "" : String(e.packs),
	packageType: e?.type ?? "",
	grossWeightKg: e?.weight == null ? "" : String(e.weight),
	cbm: e?.cbm == null ? "" : String(e.cbm),
	dimensions: e?.dims ?? "",
	note: e?.note ?? ""
}), ts = (e) => e === "Sea" ? /* @__PURE__ */ (0, R.jsx)(Na, { size: 18 }) : e === "Air" ? /* @__PURE__ */ (0, R.jsx)(pa, { size: 18 }) : e === "Rail" ? /* @__PURE__ */ (0, R.jsx)(Va, { size: 18 }) : /* @__PURE__ */ (0, R.jsx)(qa, { size: 18 });
function ns({ shipment: e, dispatch: t, toast: n }) {
	let [r, i] = (0, _.useState)(() => (e.transportLegs ?? []).map((e) => ({
		...e,
		units: (e.units ?? []).map((e) => ({ ...e }))
	}))), [a, o] = (0, _.useState)(() => es(e.cargo)), s = JSON.stringify(e.transportLegs ?? []), c = JSON.stringify(es(e.cargo));
	(0, _.useEffect)(() => {
		i((e.transportLegs ?? []).map((e) => ({
			...e,
			units: (e.units ?? []).map((e) => ({ ...e }))
		})));
	}, [e.id, s]), (0, _.useEffect)(() => {
		o(es(e.cargo));
	}, [e.id, c]);
	let l = (e, t, n) => {
		i((r) => r.map((r) => r.id === e ? {
			...r,
			[t]: n
		} : r));
	}, u = (e, t, n, r) => {
		i((i) => i.map((i) => i.id === e ? {
			...i,
			units: i.units.map((e) => e.id === t ? {
				...e,
				[n]: r
			} : e)
		} : i));
	}, d = (e, t) => {
		t !== e.mode && (e.units.length > 0 && !window.confirm("Đổi mode sẽ xóa xe/container trong bản nháp của chặng này. Tiếp tục?") || i((n) => n.map((n) => n.id === e.id ? {
			...n,
			mode: t,
			units: []
		} : n)));
	}, f = (e) => e.map((e, t) => ({
		...e,
		sequence: t + 1
	})), p = (e, t) => {
		let n = e + t;
		if (n < 0 || n >= r.length) return;
		let a = [...r];
		[a[e], a[n]] = [a[n], a[e]], i(f(a));
	}, m = (e) => {
		window.confirm(`Xóa chặng ${e.sequence} (${e.mode}) khỏi bản nháp?`) && i((t) => f(t.filter((t) => t.id !== e.id)));
	}, h = (e, t) => {
		i((n) => n.map((n) => n.id === e ? {
			...n,
			units: [...n.units, $o(t)]
		} : n));
	}, g = (e, t) => {
		let n = t.number || (t.kind === "truck" ? "xe chưa có biển số" : "container chưa có số");
		window.confirm(`Xóa ${n} khỏi bản nháp?`) && i((n) => n.map((n) => n.id === e ? {
			...n,
			units: n.units.filter((e) => e.id !== t.id)
		} : n));
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4",
		id: "missing-anchor",
		children: [
			!e.transportLegsStructured && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border border-amber-300 bg-amber-50 p-4 text-[13.5px] text-amber-950",
				children: [/* @__PURE__ */ (0, R.jsx)("p", {
					className: "font-extrabold",
					children: "Lô cũ · đang đọc dữ liệu tương thích"
				}), /* @__PURE__ */ (0, R.jsx)("p", {
					className: "mt-0.5",
					children: "Các giá trị xe/container đơn hiện có được hiển thị thành các chặng riêng. Chỉ khi bấm “Lưu các chặng”, danh sách đang thấy mới trở thành dữ liệu structured; trường cũ vẫn được giữ nguyên."
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap items-start gap-2 mb-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsxs)("h2", {
							className: "font-extrabold text-[18px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(ra, {
								size: 20,
								className: "text-[#1e5aa8]"
							}), " HÀNG HÓA"]
						}), /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-0.5",
							children: "Tóm tắt hàng của cả lô; không phải SKU/WMS. Để trống nghĩa là chưa biết."
						})] }), !e.cargoStructured && e.cargo?.qtyPkg && /* @__PURE__ */ (0, R.jsxs)("span", {
							className: "ml-auto rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-[12px] font-bold text-amber-800",
							children: ["Dữ liệu cũ: ", e.cargo.qtyPkg]
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
						children: [
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "sm:col-span-2 lg:col-span-4",
								children: /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Mô tả hàng",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										"data-field": "cargo-goods-description",
										value: a.goodsDescription,
										onChange: (e) => o((t) => ({
											...t,
											goodsDescription: e.target.value
										})),
										placeholder: "Tên/mô tả hàng thực tế",
										className: X()
									})
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Số kiện",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: a.packageCount,
									onChange: (e) => o((t) => ({
										...t,
										packageCount: e.target.value
									})),
									inputMode: "numeric",
									placeholder: "Bỏ trống = chưa biết",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Loại kiện",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: a.packageType,
									onChange: (e) => o((t) => ({
										...t,
										packageType: e.target.value
									})),
									placeholder: "Thùng / pallet / bao…",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "GW (kg)",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: a.grossWeightKg,
									onChange: (e) => o((t) => ({
										...t,
										grossWeightKg: e.target.value
									})),
									inputMode: "decimal",
									placeholder: "Bỏ trống = chưa biết",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "CBM",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: a.cbm,
									onChange: (e) => o((t) => ({
										...t,
										cbm: e.target.value
									})),
									inputMode: "decimal",
									placeholder: "Bỏ trống = chưa biết",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "sm:col-span-2",
								children: /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Kích thước",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: a.dimensions,
										onChange: (e) => o((t) => ({
											...t,
											dimensions: e.target.value
										})),
										placeholder: "VD: 120 × 80 × 100 cm / pallet",
										className: X()
									})
								})
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "sm:col-span-2",
								children: /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Ghi chú",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: a.note,
										onChange: (e) => o((t) => ({
											...t,
											note: e.target.value
										})),
										placeholder: "Ghi chú vận hành về hàng",
										className: X()
									})
								})
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)(wo, {
						onClick: () => {
							t("shipment_transport_save", {
								shipmentId: e.id,
								cargoSummary: {
									goods_description: a.goodsDescription.trim(),
									package_count: a.packageCount.trim(),
									package_type: a.packageType.trim(),
									gross_weight_kg: a.grossWeightKg.trim(),
									cbm: a.cbm.trim(),
									dimensions: a.dimensions.trim(),
									note: a.note.trim()
								}
							}) ? n("Đã gửi thông tin hàng hóa", "Ô số để trống được lưu là chưa biết, không đổi thành 0.", "green") : n("Không gửi được", "Component chưa kết nối backend.", "red");
						},
						className: "w-full sm:w-auto mt-4",
						children: [/* @__PURE__ */ (0, R.jsx)(xa, { size: 16 }), " LƯU HÀNG HÓA"]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-col sm:flex-row sm:items-start gap-3 mb-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsxs)("h2", {
							className: "font-extrabold text-[18px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(qa, {
								size: 20,
								className: "text-[#1e5aa8]"
							}), " CÁC CHẶNG VẬN CHUYỂN"]
						}), /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-0.5",
							children: "Mỗi chặng là một fact riêng; xe lấy hàng và xe giao không bị gộp."
						})] }), /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => i((e) => [...e, Qo(e.length + 1)]),
							className: "btn-press touch-target sm:ml-auto rounded-xl border-2 border-[#1e5aa8] text-[#1e5aa8] font-extrabold px-4 min-h-[46px]",
							children: "+ THÊM CHẶNG"
						})]
					}),
					r.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border-2 border-dashed border-slate-300 p-6 text-center",
						children: [/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-slate-600",
							children: "Chưa có chặng vận chuyển."
						}), /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13px] text-slate-500",
							children: "Có thể lưu lô trước và bổ sung chặng khi điều phối có dữ liệu."
						})]
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "space-y-3",
						children: r.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("details", {
							className: "group rounded-2xl border-2 border-slate-200 bg-slate-50/60 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsxs)("summary", {
								className: "cursor-pointer list-none p-3.5 md:p-4 flex flex-wrap items-center gap-2 bg-white",
								children: [
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "w-9 h-9 rounded-xl bg-[#0f2a4a] text-white grid place-items-center",
										children: ts(e.mode)
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "font-extrabold text-[#0f2a4a]",
										children: [
											"Chặng ",
											e.sequence,
											" · ",
											e.mode
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "text-[13px] text-slate-500 min-w-0 truncate",
										children: [
											e.origin || "Chưa có nơi đi",
											" → ",
											e.destination || "chưa có nơi đến"
										]
									}),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "ml-auto text-[12px] font-bold text-slate-400 group-open:hidden",
										children: "Mở để nhập"
									})
								]
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "p-3.5 md:p-4 border-t border-slate-200 space-y-4",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex flex-wrap gap-2",
										children: [
											/* @__PURE__ */ (0, R.jsx)("button", {
												onClick: () => p(t, -1),
												disabled: t === 0,
												className: "touch-target rounded-lg border bg-white px-3 text-[13px] font-bold disabled:opacity-40",
												children: "↑ Lên"
											}),
											/* @__PURE__ */ (0, R.jsx)("button", {
												onClick: () => p(t, 1),
												disabled: t === r.length - 1,
												className: "touch-target rounded-lg border bg-white px-3 text-[13px] font-bold disabled:opacity-40",
												children: "↓ Xuống"
											}),
											/* @__PURE__ */ (0, R.jsxs)("button", {
												onClick: () => m(e),
												className: "touch-target ml-auto rounded-lg border border-red-200 bg-white px-3 text-[13px] font-bold text-red-700 inline-flex items-center gap-1",
												children: [/* @__PURE__ */ (0, R.jsx)(Ua, { size: 14 }), " Xóa chặng"]
											})
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
										children: [
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Mode",
												children: /* @__PURE__ */ (0, R.jsx)("select", {
													value: e.mode,
													onChange: (t) => d(e, t.target.value),
													className: X(),
													children: Xo.map((e) => /* @__PURE__ */ (0, R.jsx)("option", { children: e }, e))
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Hãng vận chuyển",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.carrier,
													onChange: (t) => l(e.id, "carrier", t.target.value),
													placeholder: e.mode === "Air" ? "Airline" : "Carrier / nhà xe",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: e.mode === "Air" ? "Sân bay đi" : "Nơi đi",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.origin,
													onChange: (t) => l(e.id, "origin", t.target.value),
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: e.mode === "Air" ? "Sân bay đến" : "Nơi đến",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.destination,
													onChange: (t) => l(e.id, "destination", t.target.value),
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "ETD",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.etd,
													onChange: (t) => l(e.id, "etd", t.target.value),
													placeholder: "YYYY-MM-DD",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "ETA",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.eta,
													onChange: (t) => l(e.id, "eta", t.target.value),
													placeholder: "YYYY-MM-DD",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "ATD",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.atd,
													onChange: (t) => l(e.id, "atd", t.target.value),
													placeholder: "YYYY-MM-DD",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "ATA",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.ata,
													onChange: (t) => l(e.id, "ata", t.target.value),
													placeholder: "YYYY-MM-DD",
													className: X()
												})
											})
										]
									}),
									e.mode === "Sea" && /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl border border-blue-200 bg-blue-50/50 p-3.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-blue-900 mb-3",
											children: "Thông tin đường biển"
										}), /* @__PURE__ */ (0, R.jsxs)("div", {
											className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3",
											children: [
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "Booking",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.bookingNo,
														onChange: (t) => l(e.id, "bookingNo", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "Vessel",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.vessel,
														onChange: (t) => l(e.id, "vessel", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "Voyage",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.voyage,
														onChange: (t) => l(e.id, "voyage", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "MBL",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.mbl,
														onChange: (t) => l(e.id, "mbl", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "HBL",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.hbl,
														onChange: (t) => l(e.id, "hbl", t.target.value),
														className: X()
													})
												})
											]
										})]
									}),
									e.mode === "Air" && /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl border border-sky-200 bg-sky-50/60 p-3.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-sky-900 mb-3",
											children: "Thông tin hàng không"
										}), /* @__PURE__ */ (0, R.jsxs)("div", {
											className: "grid grid-cols-1 sm:grid-cols-3 gap-3",
											children: [
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "Flight no",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.flightNo,
														onChange: (t) => l(e.id, "flightNo", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "MAWB",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.mawb,
														onChange: (t) => l(e.id, "mawb", t.target.value),
														className: X()
													})
												}),
												/* @__PURE__ */ (0, R.jsx)(Y, {
													label: "HAWB",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														value: e.hawb,
														onChange: (t) => l(e.id, "hawb", t.target.value),
														className: X()
													})
												})
											]
										})]
									}),
									(e.mode === "Truck" || e.mode === "Sea") && /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "space-y-3",
										children: [/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "flex flex-wrap items-center gap-2",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "font-extrabold text-[14px] text-[#0f2a4a]",
												children: e.mode === "Truck" ? "Xe tải" : "Container"
											}), /* @__PURE__ */ (0, R.jsxs)("button", {
												onClick: () => h(e.id, e.mode === "Truck" ? "truck" : "container"),
												className: "btn-press touch-target ml-auto rounded-xl bg-[#1e5aa8] text-white font-bold px-4 min-h-[44px]",
												children: ["+ ", e.mode === "Truck" ? "Thêm xe" : "Thêm container"]
											})]
										}), e.units.map((t, n) => /* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-white border border-slate-200 p-3.5",
											children: [/* @__PURE__ */ (0, R.jsxs)("div", {
												className: "flex items-center gap-2 mb-3",
												children: [/* @__PURE__ */ (0, R.jsxs)("span", {
													className: "font-extrabold text-[13.5px] text-[#0f2a4a]",
													children: [
														t.kind === "truck" ? "Xe" : "Container",
														" ",
														n + 1
													]
												}), /* @__PURE__ */ (0, R.jsxs)("button", {
													onClick: () => g(e.id, t),
													className: "touch-target ml-auto text-red-700 text-[12.5px] font-bold inline-flex items-center gap-1",
													children: [/* @__PURE__ */ (0, R.jsx)(Ua, { size: 13 }), " Xóa"]
												})]
											}), t.kind === "truck" ? /* @__PURE__ */ (0, R.jsxs)("div", {
												className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
												children: [
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Loại / kích thước",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															"data-field": "unit-type-size",
															value: t.typeSize,
															onChange: (n) => u(e.id, t.id, "typeSize", n.target.value),
															placeholder: "VD: 17.5m / tải 30t",
															className: X()
														})
													}),
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Biển số",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															"data-field": "unit-number",
															value: t.number,
															onChange: (n) => u(e.id, t.id, "number", n.target.value),
															className: X()
														})
													}),
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Tài xế",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															value: t.driverName,
															onChange: (n) => u(e.id, t.id, "driverName", n.target.value),
															className: X()
														})
													}),
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "SĐT tài xế",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															value: t.driverPhone,
															onChange: (n) => u(e.id, t.id, "driverPhone", n.target.value),
															className: X()
														})
													})
												]
											}) : /* @__PURE__ */ (0, R.jsxs)("div", {
												className: "grid grid-cols-1 sm:grid-cols-3 gap-3",
												children: [
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Số container",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															value: t.number,
															onChange: (n) => u(e.id, t.id, "number", n.target.value),
															className: X()
														})
													}),
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Loại / kích thước",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															value: t.typeSize,
															onChange: (n) => u(e.id, t.id, "typeSize", n.target.value),
															placeholder: "20GP / 40HC",
															className: X()
														})
													}),
													/* @__PURE__ */ (0, R.jsx)(Y, {
														label: "Seal",
														children: /* @__PURE__ */ (0, R.jsx)("input", {
															value: t.sealNo,
															onChange: (n) => u(e.id, t.id, "sealNo", n.target.value),
															className: X()
														})
													})
												]
											})]
										}, t.id))]
									}),
									e.mode === "Rail" && /* @__PURE__ */ (0, R.jsx)("p", {
										className: "rounded-xl bg-slate-100 border p-3 text-[13px] text-slate-600",
										children: "Rail V1 chỉ lưu tuyến, hãng và mốc ngày chung; chưa tạo subsystem đường sắt riêng."
									})
								]
							})]
						}, e.id))
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-col sm:flex-row gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsxs)(wo, {
							onClick: () => {
								let i = f(r).map((e) => ({
									id: e.id,
									sequence: e.sequence,
									mode: e.mode,
									origin: e.origin.trim(),
									destination: e.destination.trim(),
									carrier: e.carrier.trim(),
									etd: e.etd.trim(),
									eta: e.eta.trim(),
									atd: e.atd.trim(),
									ata: e.ata.trim(),
									booking_no: e.bookingNo.trim(),
									mbl: e.mbl.trim(),
									hbl: e.hbl.trim(),
									vessel: e.vessel.trim(),
									voyage: e.voyage.trim(),
									mawb: e.mawb.trim(),
									hawb: e.hawb.trim(),
									flight_no: e.flightNo.trim(),
									units: e.units.map((e) => ({
										id: e.id,
										kind: e.kind,
										number: e.number.trim(),
										type_size: e.typeSize.trim(),
										seal_no: e.sealNo.trim(),
										driver_name: e.driverName.trim(),
										driver_phone: e.driverPhone.trim()
									}))
								}));
								t("shipment_transport_save", {
									shipmentId: e.id,
									transportLegs: i
								}) ? n("Đã gửi các chặng vận chuyển", "Backend kiểm tra ID/thứ tự/mode rồi ghi atomic và đọc lại.", "green") : n("Không gửi được", "Component chưa kết nối backend.", "red");
							},
							className: "flex-1",
							children: [/* @__PURE__ */ (0, R.jsx)(xa, { size: 16 }), " LƯU CÁC CHẶNG"]
						}), /* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: () => i((e.transportLegs ?? []).map((e) => ({
								...e,
								units: (e.units ?? []).map((e) => ({ ...e }))
							}))),
							children: "Hoàn tác bản nháp"
						})]
					})
				]
			})
		]
	});
}
//#endregion
//#region src/components/FinanceActualEntry.tsx
var rs = {
	id: "",
	code: "",
	name: "",
	unit: "",
	qty: "1",
	cost: "",
	price: "",
	vat: "",
	note: ""
};
function is(e) {
	return {
		id: e.id ?? "",
		code: e.code ?? "",
		name: e.name || e.label || "",
		unit: e.unit ?? "",
		qty: e.qty == null ? "" : String(e.qty),
		cost: e.cost == null ? "" : String(e.cost),
		price: e.price == null ? "" : String(e.price),
		vat: e.vat == null ? "" : String(e.vat),
		note: e.note ?? ""
	};
}
var as = () => `FACTUAL-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
function os({ label: e, className: t, children: n }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: U("min-w-0", t),
		children: [/* @__PURE__ */ (0, R.jsx)("span", {
			className: "block md:hidden text-[11px] font-extrabold uppercase tracking-wide text-slate-400",
			children: e
		}), n]
	});
}
function ss({ shipment: e, services: t, ccy: n, dispatch: r, toast: i, lastWrites: a }) {
	let o = e.finance.actual ?? [], [s, c] = (0, _.useState)(rs), [l, u] = (0, _.useState)(!1), [d, f] = (0, _.useState)(""), [p, m] = (0, _.useState)(""), [h, g] = (0, _.useState)(null), v = (0, _.useRef)(null);
	(0, _.useEffect)(() => {
		u(!1), c(rs), f(""), m(""), g(null);
	}, [e.id]);
	let y = (0, _.useMemo)(() => {
		let e = /* @__PURE__ */ new Map();
		for (let n of t) e.set(n.code, n);
		return e;
	}, [t]), b = (0, _.useMemo)(() => {
		let e = [], n = /* @__PURE__ */ new Map();
		for (let r of t) {
			let t = r.group || "DỊCH VỤ";
			n.has(t) || (n.set(t, e.length), e.push({
				group: t,
				entries: []
			})), e[n.get(t)].entries.push(r);
		}
		return e;
	}, [t]), x = (() => {
		if (!s.id) return !1;
		let e = y.get(s.code);
		return !e || e.name.trim() !== s.name.trim();
	})(), S = (e) => {
		c(e ? is(e) : rs), f(""), m(""), g(null), u(!0), window.setTimeout(() => v.current?.scrollIntoView({
			behavior: "smooth",
			block: "center"
		}), 60);
	}, C = () => {
		u(!1), c(rs), f(""), m(""), g(null);
	}, w = (e, t) => {
		c((n) => ({
			...n,
			[e]: t
		})), f("");
	}, T = (e) => {
		let t = e ? y.get(e) : void 0;
		if (!t) {
			c((e) => ({
				...e,
				code: "",
				name: "",
				unit: ""
			})), f("");
			return;
		}
		c((e) => ({
			...e,
			code: t.code,
			name: t.name,
			unit: t.unit || "Lần"
		})), f("");
	}, E = (0, _.useMemo)(() => {
		let e = yo(s.qty), t = yo(s.price), n = yo(s.cost), r = yo(s.vat), i = e != null && t != null ? e * t : null;
		return {
			net: i,
			withVat: i != null && r != null ? i * (1 + r / 100) : null,
			costTotal: e != null && n != null ? e * n : null
		};
	}, [
		s.qty,
		s.price,
		s.cost,
		s.vat
	]);
	return (0, _.useEffect)(() => {
		if (!h) return;
		let e = (a ?? []).find((e) => e.event === "finance_actual_save" && e.requestId === h.requestId);
		if (e) {
			if (e.ok) {
				let e = h.mode;
				C(), i(e === "edit" ? "Đã cập nhật dòng thực tế" : "Đã ghi nhận dịch vụ thực tế", "Backend lưu vào data['3.4'].details, tính lại phải thu · chi phí · lợi nhuận rồi đọc lại dữ liệu mới.", "green");
			} else {
				let t = e.error || "Backend từ chối dòng thực tế này.";
				g(null), m(t), i("Chưa lưu được dòng thực tế", t, "red");
			}
		}
	}, [a, h]), /* @__PURE__ */ (0, R.jsxs)("section", {
		className: "rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5",
		id: "finance-actual-lines",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex flex-col sm:flex-row sm:items-start gap-3 mb-1",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "min-w-0",
					children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
						className: "font-extrabold text-[16.5px] md:text-[18px] text-[#0f2a4a] flex items-center gap-2",
						children: [/* @__PURE__ */ (0, R.jsx)(_a, {
							size: 20,
							className: "text-emerald-600"
						}), " DỊCH VỤ & CHI PHÍ THỰC TẾ"]
					}), /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13px] text-slate-500 mt-0.5",
						children: [
							"Giá vốn · giá bán · VAT cho từng dịch vụ của lô, tiền ",
							n,
							" — không quy đổi. Sai thì sửa đúng dòng đó, không xóa lịch sử."
						]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("button", {
					onClick: () => l && !s.id ? C() : S(null),
					className: "btn-press touch-target sm:ml-auto shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8] bg-white text-[#1e5aa8] font-extrabold px-4 min-h-[46px]",
					children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " THÊM DỊCH VỤ / CHI PHÍ"]
				})]
			}),
			o.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "mt-3 rounded-xl border-2 border-dashed border-slate-300 p-5 text-center",
				children: [/* @__PURE__ */ (0, R.jsx)("p", {
					className: "font-bold text-slate-600 text-[14.5px]",
					children: "Chưa có dòng dịch vụ thực tế nào cho lô này."
				}), /* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[13px] text-slate-500 mt-1",
					children: "Bấm “+ THÊM DỊCH VỤ / CHI PHÍ” để ghi nhận. Doanh thu · chi phí · lợi nhuận thực tế đang chưa xác định, không phải 0."
				})]
			}),
			o.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "mt-3 rounded-xl border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "hidden md:grid md:grid-cols-12 gap-2 px-3 py-2 bg-slate-50 border-b border-slate-200 text-[11.5px] font-extrabold uppercase tracking-wide text-slate-500",
					children: [
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-3",
							children: "Dịch vụ"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-2",
							children: "Mã"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-1 text-right",
							children: "SL"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-1",
							children: "Đơn vị"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-2 text-right",
							children: "Giá vốn"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-2 text-right",
							children: "Giá bán"
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "md:col-span-1 text-right",
							children: "VAT"
						})
					]
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "divide-y divide-slate-100",
					children: o.map((e, t) => {
						let r = e.qty != null && e.amount != null ? e.qty * e.amount : null;
						return /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "p-3",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-2 md:grid-cols-12 gap-x-2 gap-y-1.5 items-baseline",
								children: [
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "Dịch vụ",
										className: "col-span-2 md:col-span-3",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[14.5px] text-[#0f2a4a] block",
											title: e.label,
											children: e.label
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "Mã",
										className: "md:col-span-2",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[13px] font-bold text-slate-500",
											children: K(e.code)
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "SL",
										className: "md:col-span-1 text-left md:text-right",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[14px] font-semibold",
											children: bo(e.qty)
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "Đơn vị",
										className: "md:col-span-1",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[13.5px] text-slate-600",
											children: K(e.unit)
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "Giá vốn",
										className: "md:col-span-2 text-right",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[14px] font-semibold text-slate-700",
											children: G(e.cost, e.ccy ?? n)
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "Giá bán",
										className: "md:col-span-2 text-right",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[14.5px] font-extrabold",
											children: G(e.amount, e.ccy ?? n)
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(os, {
										label: "VAT",
										className: "md:col-span-1 text-left md:text-right",
										children: /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[13.5px] font-semibold text-slate-600",
											children: e.vat == null ? "—" : `VAT ${bo(e.vat)}%`
										})
									})
								]
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-1.5 flex flex-wrap items-center gap-2",
								children: [/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "text-[12.5px] text-slate-500 flex-1 min-w-[150px]",
									children: [
										"Ghi chú: ",
										e.note && e.note.trim() ? e.note : "—",
										r == null ? "" : ` · Thành tiền dòng ${W(r)} ${e.ccy ?? n}`
									]
								}), /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => S(e),
									disabled: !e.id,
									title: e.id ? "Sửa đúng dòng này — dòng cũ được cập nhật tại chỗ, không thêm dòng mới" : "Dòng chưa có mã định danh — chưa sửa được qua màn hình này",
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 bg-white text-[#1e5aa8] text-[13px] font-bold px-3 min-h-[40px] disabled:opacity-40",
									children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " SỬA"]
								})]
							})]
						}, e.id || `${e.label}-${t}`);
					})
				})]
			}),
			l && /* @__PURE__ */ (0, R.jsxs)("div", {
				ref: v,
				className: "mt-3 rounded-xl border-2 border-[#1e5aa8] bg-blue-50/40 p-3.5 md:p-4",
				id: "finance-actual-form",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-start gap-2 mb-2.5",
						children: [/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-extrabold text-[15px] text-[#0f2a4a]",
							children: s.id ? `SỬA DÒNG THỰC TẾ · ${s.id}` : "THÊM DỊCH VỤ / CHI PHÍ THỰC TẾ"
						}), /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: C,
							"aria-label": "Đóng form",
							className: "ml-auto touch-target rounded-lg p-1.5 text-slate-500 hover:bg-white",
							children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 18 })
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 md:grid-cols-12 gap-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "md:col-span-5",
								children: x ? /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Dịch vụ (dòng cũ)",
									required: !0,
									hint: "Dòng này không thuộc danh mục — tên đang lưu được giữ nguyên.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: s.name,
										onChange: (e) => w("name", e.target.value),
										className: X(s.name.trim() ? "ok" : "missing")
									})
								}) : /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Dịch vụ",
									required: !0,
									hint: t.length === 0 ? "Danh mục dịch vụ chưa được tải từ backend" : "Danh mục dùng chung của app",
									children: /* @__PURE__ */ (0, R.jsxs)("select", {
										value: y.has(s.code) ? s.code : "",
										onChange: (e) => T(e.target.value),
										className: X(s.name ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, R.jsx)("option", {
											value: "",
											children: "— Chọn dịch vụ —"
										}), b.map((e) => /* @__PURE__ */ (0, R.jsx)("optgroup", {
											label: e.group,
											children: e.entries.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
												value: e.code,
												children: [
													e.name,
													" (",
													e.code,
													")"
												]
											}, e.code))
										}, e.group))]
									})
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Mã dịch vụ",
								hint: "Tự lấy theo dịch vụ đã chọn",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.code,
									readOnly: !0,
									placeholder: "—",
									className: U(X(), "bg-slate-100 font-bold")
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Đơn vị",
								hint: "Thường là Lần",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.unit,
									onChange: (e) => w("unit", e.target.value),
									placeholder: "Lần",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Số lượng",
								hint: "Mặc định 1",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.qty,
									onChange: (e) => w("qty", e.target.value),
									inputMode: "decimal",
									placeholder: "1",
									className: X()
								})
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-12 gap-2.5 mt-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: `Giá vốn (${n})`,
								required: !0,
								hint: "Chi phí thực tế đã trả cho dịch vụ này",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.cost,
									onChange: (e) => w("cost", e.target.value),
									inputMode: "decimal",
									placeholder: "VD: 57000000",
									className: X(s.cost.trim() ? "ok" : "missing")
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: `Giá bán (${n})`,
								required: !0,
								hint: "Giá bán thực tế cho khách",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.price,
									onChange: (e) => w("price", e.target.value),
									inputMode: "decimal",
									placeholder: "VD: 62000000",
									className: X(s.price.trim() ? "ok" : "missing")
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "VAT %",
								required: !0,
								hint: "Phải tự nhập — 0 là giá trị hợp lệ (không VAT)",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: s.vat,
									onChange: (e) => w("vat", e.target.value),
									inputMode: "decimal",
									placeholder: "VD: 8",
									className: X(s.vat.trim() ? "ok" : "missing")
								})
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "sm:col-span-2 md:col-span-9",
								children: /* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Ghi chú",
									hint: "Không bắt buộc — VD: số hóa đơn, người chốt",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: s.note,
										onChange: (e) => w("note", e.target.value),
										placeholder: "Ghi chú cho dòng này",
										className: X()
									})
								})
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13px] text-slate-600 mt-2.5",
						children: [
							"Tạm tính từ số vừa nhập (chỉ để soát, không phải số lưu): doanh thu ",
							n,
							" ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: E.net == null ? "—" : W(E.net) }),
							" · ",
							"sau VAT ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: E.withVat == null ? "—" : W(E.withVat) }),
							" · ",
							"chi phí ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: E.costTotal == null ? "—" : W(E.costTotal) }),
							". Số chính thức của lô do backend tính khi lưu."
						]
					}),
					(d || p) && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-2.5 rounded-xl border-2 border-red-300 bg-red-50 p-3 text-[13.5px] text-red-800 flex items-start gap-2",
						children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
							size: 17,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsx)("span", { children: d || p })]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: C,
							className: "min-h-[48px]",
							children: "HỦY, KHÔNG LƯU"
						}), /* @__PURE__ */ (0, R.jsxs)(wo, {
							onClick: () => {
								let t = s.name.trim();
								if (!t) {
									f("Chọn dịch vụ trong danh mục — dòng thực tế không được để trống tên.");
									return;
								}
								let n = [], i = [
									["Giá bán", s.price],
									["Giá vốn", s.cost],
									["VAT %", s.vat]
								];
								for (let [e, t] of i) t.trim() ? yo(t) ?? n.push(`${e} không phải số`) : n.push(`${e} chưa nhập`);
								let a = s.qty.trim(), o = yo(a);
								if (a && o == null ? n.push("Số lượng không phải số") : o != null && o <= 0 && n.push("Số lượng phải lớn hơn 0"), n.length > 0) {
									f(`${n.join(" · ")}. Dòng thực tế phải nêu rõ số tiền — 0 là giá trị hợp lệ, để trống thì không.`);
									return;
								}
								if (!s.id && !y.has(s.code)) {
									f("Chọn dịch vụ từ danh mục để lấy mã phí và đơn vị tính.");
									return;
								}
								let c = as(), l = {
									name: t,
									code: s.code,
									unit: s.unit.trim() || "Lần",
									qty: a,
									cost: s.cost.trim(),
									price: s.price.trim(),
									vat: s.vat.trim(),
									note: s.note.trim()
								};
								if (s.id && (l.id = s.id), !r("finance_actual_save", {
									shipmentId: e.id,
									line: l,
									requestId: c
								})) {
									f("Component chưa kết nối backend — dữ liệu chưa được gửi đi.");
									return;
								}
								m(""), g({
									requestId: c,
									mode: s.id ? "edit" : "new"
								});
							},
							className: "min-h-[48px]",
							disabled: h != null,
							children: [
								/* @__PURE__ */ (0, R.jsx)(xa, { size: 16 }),
								" ",
								s.id ? "💾 LƯU LẠI DÒNG NÀY" : "💾 LƯU DÒNG THỰC TẾ"
							]
						})]
					})
				]
			})
		]
	});
}
//#endregion
//#region src/components/ShipmentAttachments.tsx
function cs(e) {
	return `${e}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}
var ls = {
	allowUpload: !1,
	categories: [],
	allowedExtensions: [],
	accept: "",
	maxUploadBytes: 0,
	maxUploadLabel: "",
	storageBackend: "gridfs",
	storageConfigured: !1,
	storageLabel: "Kho chứng từ"
};
function us({ shipmentId: e, attachments: t, policy: n }) {
	let { dispatch: r, toast: i } = Jn(), a = (0, _.useSyncExternalStore)(C, S, S)?.lastWrites ?? [], o = n ?? ls, s = o.storageLabel || (o.driveConfigured ? "Shared Drive" : "Kho chứng từ"), c = o.storageConfigured ?? o.driveConfigured ?? !1, l = (0, _.useRef)(null), [u, d] = (0, _.useState)(o.categories[0]?.id ?? "other"), [f, p] = (0, _.useState)(null), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(null), [y, b] = (0, _.useState)(""), [x, w] = (0, _.useState)(""), [T, E] = (0, _.useState)(!1), D = (0, _.useRef)({});
	(0, _.useEffect)(() => {
		if (!m) return;
		let e = a.find((e) => e.event === "shipment_attachment_upload" && e.requestId === m);
		if (!e) return;
		h(""), E(!!e.ok);
		let t = String(e.message || e.error || "");
		w(t || (e.ok ? "Đã lưu tệp đính kèm vào lô." : "Tải tệp thất bại.")), e.ok && (p(null), l.current && (l.current.value = ""));
	}, [a, m]), (0, _.useEffect)(() => {
		if (!g) return;
		let e = a.find((e) => e.event === "attachment_download" && e.requestId === g.requestId);
		e && (v(null), e.ok || (E(!1), w(String(e.error || `Không đọc được tệp từ ${s}.`))));
	}, [a, g]), (0, _.useEffect)(() => {
		for (let e of t) {
			if (!e.downloadAvailable || !e.downloadBase64) continue;
			let t = e.downloadSeq ?? 0;
			D.current[e.id] !== t && (D.current[e.id] = t, xo(e.name, e.downloadBase64, e.mime || "application/octet-stream"), i("Đã tải " + e.name, `Bytes đọc từ ${s.toLowerCase()} qua máy chủ.`, "green"));
		}
	}, [t, i]);
	let O = o.accept || void 0, k = () => {
		if (b(""), w(""), !f) {
			b("Chưa chọn tệp.");
			return;
		}
		if (o.maxUploadBytes > 0 && f.size > o.maxUploadBytes) {
			b(`Tệp vượt giới hạn ${o.maxUploadLabel}. Chưa gửi lên máy chủ.`);
			return;
		}
		let t = cs("ATT");
		h(t);
		let n = new FileReader();
		n.onerror = () => {
			h(""), b("Không đọc được nội dung tệp đã chọn.");
		}, n.onload = () => {
			let i = typeof n.result == "string" ? n.result : "", a = i.indexOf(","), o = a >= 0 ? i.slice(a + 1) : i;
			if (!o) {
				h(""), b("Tệp không có dữ liệu.");
				return;
			}
			r("shipment_attachment_upload", {
				shipmentId: e,
				category: u,
				fileName: f.name,
				mime: f.type,
				size: f.size,
				base64: o,
				requestId: t
			}) || (h(""), b("Không gửi được tệp tới backend."));
		}, n.readAsDataURL(f);
	}, A = (t) => {
		b(""), w("");
		let n = cs("ATTDOWN");
		v({
			requestId: n,
			attachmentId: t.id
		}), r("attachment_download", {
			shipmentId: e,
			attachmentId: t.id,
			requestId: n
		}) || (v(null), b("Không gửi được yêu cầu mở tệp tới backend."));
	}, ee = Array.isArray(t) ? t : [];
	return /* @__PURE__ */ (0, R.jsxs)("section", {
		className: "mt-4 rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
		"data-testid": "shipment-attachments",
		children: [
			/* @__PURE__ */ (0, R.jsx)(J, {
				icon: /* @__PURE__ */ (0, R.jsx)(aa, {
					size: 19,
					className: "text-[#1e5aa8]"
				}),
				title: "Tệp đính kèm lô hàng",
				sub: `Tệp thật của lô: nội dung tệp được lưu trong ${s}; thông tin mô tả được lưu cùng hồ sơ lô.`,
				right: /* @__PURE__ */ (0, R.jsxs)(q, {
					tone: ee.length > 0 ? "green" : "gray",
					size: "sm",
					children: [ee.length, " tệp"]
				})
			}),
			o.allowUpload ? /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1",
				children: [/* @__PURE__ */ (0, R.jsxs)("label", {
					className: "block min-w-0",
					children: [/* @__PURE__ */ (0, R.jsx)("span", {
						className: "block text-[13px] font-bold text-slate-600 mb-1",
						children: "Loại chứng từ"
					}), /* @__PURE__ */ (0, R.jsx)("select", {
						id: "fld-attach-category",
						"data-testid": "attachment-category",
						value: u,
						onChange: (e) => d(e.target.value),
						className: X(),
						children: o.categories.map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
							value: e.id,
							children: e.label
						}, e.id))
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("label", {
					className: "block min-w-0",
					children: [/* @__PURE__ */ (0, R.jsxs)("span", {
						className: "block text-[13px] font-bold text-slate-600 mb-1",
						children: [
							"Chọn file (tối đa ",
							o.maxUploadLabel || "20 MB",
							")"
						]
					}), /* @__PURE__ */ (0, R.jsx)("input", {
						ref: l,
						id: "fld-attach-file",
						"data-testid": "attachment-file",
						type: "file",
						accept: O,
						onChange: (e) => {
							p(e.target.files?.[0] ?? null), b(""), w("");
						},
						className: U("w-full max-w-full rounded-xl border-2 border-slate-200 bg-white px-3 py-2.5 text-[14px] min-h-[44px]", "file:mr-3 file:rounded-lg file:border-0 file:bg-[#0f2a4a] file:px-3 file:py-2 file:text-white file:font-bold")
					})]
				})]
			}) : /* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-[13.5px] text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5",
				"data-testid": "attachment-readonly",
				children: "Vai trò hiện tại chỉ được xem và tải tệp đính kèm — không được tải lên. Cần quyền sales_write."
			}),
			o.allowUpload && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "mt-3 flex flex-wrap items-center gap-2",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("button", {
						type: "button",
						"data-testid": "attachment-upload",
						disabled: !f || !!m,
						onClick: k,
						className: U("btn-press touch-target inline-flex items-center gap-2 rounded-xl px-5 min-h-[48px] font-extrabold", !f || m ? "bg-slate-300 text-slate-600" : "bg-[#0f2a4a] text-white"),
						children: [m ? /* @__PURE__ */ (0, R.jsx)(Ui, {
							size: 17,
							className: "animate-spin"
						}) : /* @__PURE__ */ (0, R.jsx)(ni, { size: 17 }), m ? `ĐANG LƯU VÀO ${s.toUpperCase()}…` : `LƯU VÀO ${s.toUpperCase()}`]
					}),
					f && /* @__PURE__ */ (0, R.jsx)("span", {
						className: "text-[13px] text-slate-600 min-w-0 break-words",
						children: f.name
					}),
					!c && /* @__PURE__ */ (0, R.jsxs)("span", {
						className: "text-[13px] text-amber-800",
						"data-testid": "attachment-storage-state",
						children: [s, " chưa sẵn sàng trên máy chủ — hệ thống sẽ từ chối trung thực."]
					})
				]
			}),
			y && /* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-3 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-[13.5px] font-semibold text-red-700",
				"data-testid": "attachment-local-error",
				children: y
			}),
			x && /* @__PURE__ */ (0, R.jsx)("p", {
				"data-testid": "attachment-outcome",
				className: U("mt-3 rounded-xl border px-3 py-2 text-[13.5px] font-semibold", T ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-amber-50 border-amber-200 text-amber-900"),
				children: x
			}),
			ee.length === 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-3 text-slate-500 text-[14px]",
				"data-testid": "attachment-empty",
				children: "Lô chưa có tệp đính kèm nào."
			}) : /* @__PURE__ */ (0, R.jsx)("ul", {
				className: "mt-3 space-y-2",
				"data-testid": "attachment-list",
				children: ee.map((e) => /* @__PURE__ */ (0, R.jsxs)("li", {
					"data-testid": "attachment-row",
					"data-attachment-id": e.id,
					className: "flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-slate-200 p-3 min-w-0",
					children: [
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: "w-8 h-8 rounded-lg grid place-items-center bg-slate-100 text-[#0f2a4a] shrink-0",
							children: /* @__PURE__ */ (0, R.jsx)(gi, { size: 17 })
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "min-w-0 flex-1",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-bold text-[14.5px] text-[#0f2a4a] break-words",
									children: e.name
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] text-slate-500 break-words",
									children: [
										e.categoryLabel,
										" · ",
										e.sizeLabel,
										" · ",
										e.uploadedAt || "—",
										e.uploadedBy ? ` · ${e.uploadedBy}` : ""
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] font-semibold text-slate-500",
									children: [e.compressionLabel, e.compressionLabel === "Ảnh đã tối ưu" && e.compressionNote ? ` — ${e.compressionNote}` : ""]
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							type: "button",
							"data-testid": "attachment-download",
							disabled: !!g,
							onClick: () => A(e),
							className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#0f2a4a] text-[#0f2a4a] font-bold px-4 min-h-[44px] shrink-0",
							children: [g?.attachmentId === e.id ? /* @__PURE__ */ (0, R.jsx)(Ui, {
								size: 15,
								className: "animate-spin"
							}) : /* @__PURE__ */ (0, R.jsx)(ci, { size: 15 }), "TẢI"]
						})
					]
				}, e.id))
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-3 text-[12.5px] text-slate-500",
				children: "Tệp trùng trong cùng lô không được lưu bản sao lần hai. Tệp giữ nguyên quyền riêng tư trong kho chứng từ — hệ thống không tạo liên kết công khai."
			})
		]
	});
}
//#endregion
//#region src/pages/ShipmentDetail.tsx
var ds = [
	{
		id: "van-tai",
		label: "Vận chuyển & Hàng hóa",
		short: "Vận chuyển"
	},
	{
		id: "lay-hang",
		label: "Xuất khẩu",
		short: "Xuất khẩu"
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
], fs = new Set(ds.map((e) => e.id));
function ps(e) {
	return `${e}-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}
function ms(e) {
	let t = e.indexOf("?");
	if (t < 0) return null;
	let n = new URLSearchParams(e.slice(t + 1)).get("tab");
	return n && fs.has(n) ? n : null;
}
function hs() {
	let { id: e } = xt(), [t, n] = Rn(), r = t.get("tab") || "van-tai", { shipments: i, updateShipment: a, toast: o, contracts: s, customers: c, dispatch: l, financeServices: u } = Jn(), d = (0, _.useSyncExternalStore)(C, S, S), f = yt(), p = i.find((t) => t.id === e), [m, h] = (0, _.useState)(!1), [g, v] = (0, _.useState)(!1), [y, b] = (0, _.useState)(!1), [x, w] = (0, _.useState)(""), [T, E] = (0, _.useState)("Thu tiền khách"), [D, O] = (0, _.useState)(""), [k, A] = (0, _.useState)({}), [ee, j] = (0, _.useState)(0);
	(0, _.useEffect)(() => {
		A({}), O("");
	}, [e, r]);
	let M = (e, t) => A((n) => ({
		...n,
		[e]: t
	})), N = (e, t) => k[e] ?? t, te = (0, _.useMemo)(() => s.find((e) => e.id === p?.contract), [s, p]);
	if (!p) return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "font-extrabold text-[19px]",
				children: ["Không tìm thấy lô ", e]
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-slate-500 mt-1 text-[15px]",
				children: "Mã lô có thể sai. Về danh sách để tìm lại."
			}),
			/* @__PURE__ */ (0, R.jsx)(L, {
				to: "/lo-hang",
				className: "btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center",
				children: "Về danh sách lô"
			})
		]
	});
	let P = p.finance.currency || "VND", F = (e) => {
		let t = {};
		for (let [n, r] of Object.entries(e)) {
			let e = (r ?? "").trim();
			e.length > 0 && (t[n] = e);
		}
		return t;
	}, ne = (e, t = []) => {
		A((e) => {
			if (t.length === 0) return {};
			let n = {};
			for (let r of t) e[r] != null && (n[r] = e[r]);
			return n;
		}), j(Date.now()), o(e, "Đã gửi tới backend. Dữ liệu sẽ được đọc lại từ Logistics sau khi ghi.", "green");
	}, re = () => {
		let e = N("tk", p.importInfo.declarationNo);
		if (!e) {
			o("Chưa thể lưu thông quan", "Thiếu: Số tờ khai nhập khẩu — nhập số TK (12 số) rồi bấm Lưu.", "red");
			return;
		}
		let t = {};
		k.tkDate != null && (t.tk_date = k.tkDate.trim()), k.importDuty != null && (t.import_duty_amount = k.importDuty.trim()), k.importVat != null && (t.import_vat_amount = k.importVat.trim());
		let n = {
			tk_no: e,
			...F({
				phan_luong: N("inspection", p.importInfo.inspection),
				arrival_date: N("arrivalDate", p.importInfo.arrivalDate ?? ""),
				free_time: N("freeTime", p.importInfo.freeTime == null ? "" : String(p.importInfo.freeTime)),
				delivery_date: N("schedule", p.importInfo.schedule)
			}),
			...t
		};
		l("shipment_field_save", {
			shipmentId: p.id,
			fields: n
		}), ne("Đã lưu tờ khai " + e);
	}, ie = () => {
		let e = k.createdAt == null ? null : k.createdAt.trim();
		if (e === null) {
			o("Chưa sửa ngày", "Chọn/ghi Ngày tạo rồi bấm Lưu — app không tự điền hôm nay.", "amber");
			return;
		}
		l("shipment_field_save", {
			shipmentId: p.id,
			fields: { created_at: e }
		}), ne(e ? "Đã lưu ngày tạo " + e : "Đã xoá ngày tạo (để trống = chưa biết)");
	}, ae = () => {
		let e = (k.lotCustomer ?? "").trim();
		if (!e || e === (p.customerId ?? "")) {
			o("Chưa đổi khách hàng", "Bấm “Tìm / đổi”, chọn khách trong danh bạ rồi bấm Lưu.", "amber");
			return;
		}
		l("shipment_customer_save", {
			shipmentId: p.id,
			customerId: e
		}), A((e) => ({
			...e,
			lotCustomer: ""
		})), ne("Đã gửi đổi khách hàng của lô");
	}, oe = () => {
		let e = l("delivery_confirm", {
			shipmentId: p.id,
			deliveredAt: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			receiverName: p.importInfo.receiver,
			receiverTitle: p.importInfo.receiverTitle ?? "",
			receiverPhone: p.importInfo.receiverPhone,
			deliveryLocation: p.importInfo.deliveryLocation || p.importInfo.deliveryAddr
		});
		v(!1), e ? o("Đã gửi xác nhận giao hàng " + p.id, "Backend ghi nhận + audit; PXK sẽ mở ở tab Chứng từ.", "green") : o("Không gửi được", "Component chưa kết nối backend.", "red");
	}, I = (0, _.useRef)(""), [se, ce] = (0, _.useState)(""), le = (0, _.useRef)(""), [ue, de] = (0, _.useState)(""), fe = () => {
		I.current = ps("PAY"), le.current = "", ce(""), de(""), h(!0);
	}, pe = () => {
		le.current = "", ce("");
	}, me = () => {
		if (le.current) return;
		let e = x.trim(), t = yo(e);
		if (t == null || t <= 0) {
			o("Chưa nhập số tiền", `Nhập số tiền ${P} rồi bấm Lưu — ví dụ 50.000.000.`, "red");
			return;
		}
		if (!l("payment_record", {
			shipmentId: p.id,
			amount: e,
			requestId: I.current,
			date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			note: T
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		de(""), le.current = I.current, ce(I.current);
	};
	(0, _.useEffect)(() => {
		if (!se) return;
		let e = (d?.lastWrites ?? []).find((e) => e.event === "payment_record" && e.requestId === se);
		if (e) {
			if (e.ok) {
				if (!(d?.shipments ?? []).find((e) => e.id === p.id)?.finance?.payments?.some((e) => e.requestId === se)) return;
				h(!1), w(""), de(""), pe(), o("Đã ghi nhận khoản thu " + p.id, "Backend đã xác nhận ghi sổ — khoản thu với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.", "green");
			} else pe(), de(e.error || "Backend từ chối khoản thu này."), I.current = ps("PAY"), o("Chưa ghi nhận được", e.error || "Backend từ chối khoản thu.", "red");
		}
	}, [d?.lastWrites, se]);
	let [he, ge] = (0, _.useState)(null), [_e, ve] = (0, _.useState)(""), [ye, be] = (0, _.useState)(""), [xe, Se] = (0, _.useState)(""), [Ce, we] = (0, _.useState)(""), [Te, Ee] = (0, _.useState)(""), [De, Oe] = (0, _.useState)(""), ke = (0, _.useRef)(""), Ae = (0, _.useRef)(""), je = (e) => {
		ke.current = ps("CORR"), Ae.current = "", ge(e), ve(""), be(""), Se(""), we(""), Ee(""), Oe("");
	}, Me = () => {
		ge(null), Ae.current = "", Oe("");
	}, Ne = () => {
		if (!he || Ae.current) return;
		let e = _e.trim();
		if (!e) {
			Ee("LÝ DO ĐIỀU CHỈNH là bắt buộc — backend từ chối correction không có lý do.");
			return;
		}
		let t = ye.trim();
		if (t && yo(t) == null) {
			Ee("Số tiền bằng chứng không phải số hợp lệ — sửa lại hoặc để trống (không tự thành 0).");
			return;
		}
		if (!l("payment_correction", {
			shipmentId: p.id,
			paymentId: he.id,
			correctionRequestId: ke.current,
			reason: e,
			...t ? { amount: t } : {},
			...xe.trim() ? { date: xe.trim() } : {},
			...Ce.trim() ? { note: Ce.trim() } : {}
		})) {
			Ee("Component chưa kết nối backend — yêu cầu chưa được gửi đi.");
			return;
		}
		Ee(""), Ae.current = ke.current, Oe(ke.current);
	};
	(0, _.useEffect)(() => {
		if (!De) return;
		let e = (d?.lastWrites ?? []).find((e) => e.event === "payment_correction" && e.correctionRequestId === De);
		e && (e.ok ? (Me(), o("Đã ghi bút toán hoàn tác có liên kết", "financial_corrections + audit payment_reversed; khoản thu gốc vẫn ở lại lịch sử với trạng thái Đã hoàn tác, số liệu đọc lại từ backend.", "green")) : (Ae.current = "", Oe(""), Ee(e.error || "Backend từ chối bút toán điều chỉnh này."), ke.current = ps("CORR"), o("Chưa điều chỉnh được", e.error || "Backend từ chối.", "red")));
	}, [d?.lastWrites, De]);
	let Pe = (0, _.useRef)(""), Fe = (0, _.useRef)(""), [Ie, Le] = (0, _.useState)({}), Re = (0, _.useRef)({}), [ze, Be] = (0, _.useState)({}), Ve = (e) => ps(e), He = () => {
		Pe.current = Ve("POBL");
	}, Ue = () => {
		Fe.current = Ve("PPAY");
	}, We = (e, t, n) => {
		Re.current = {
			...Re.current,
			[e]: t
		}, Le((n) => ({
			...n,
			[e]: t
		})), Be((t) => ({
			...t,
			[e]: n
		}));
	}, Ge = () => {
		if (Re.current.obl) return;
		let e = p.finance.partner;
		if (!e?.partnerId) {
			o("Chưa chọn đối tác", "Chưa có đối tác trong danh mục để ghi nhận phải trả.", "red");
			return;
		}
		let t = D.trim(), n = yo(t);
		if (n == null || n <= 0) {
			o("Chưa nhập số tiền", `Nhập số tiền phải trả ${P} — ví dụ 57.000.000.`, "red");
			return;
		}
		if (Pe.current || He(), !l("partner_payable_record", {
			shipmentId: p.id,
			partnerId: e.partnerId,
			amount: t,
			currency: P,
			requestId: Pe.current,
			note: "Phải trả chi phí đối tác theo thực tế lô"
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		We("obl", Pe.current, "");
	}, Ke = () => {
		if (Re.current.pay) return;
		let e = p.finance.partner;
		if (!e?.partnerId) {
			o("Chưa chọn đối tác", "Chưa có đối tác để thanh toán — ghi nhận phải trả trước.", "red");
			return;
		}
		let t = D.trim(), n = yo(t);
		if (n == null || n <= 0) {
			o("Chưa nhập số tiền", `Nhập số tiền thanh toán ${P} — ví dụ 20.000.000.`, "red");
			return;
		}
		if (Fe.current || Ue(), !l("partner_payment_record", {
			shipmentId: p.id,
			partnerId: e.partnerId,
			amount: t,
			currency: P,
			requestId: Fe.current,
			date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
			note: "Chuyển khoản thanh toán đối tác"
		})) {
			o("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		We("pay", Fe.current, "");
	};
	(0, _.useEffect)(() => {
		let e = d?.lastWrites ?? [];
		if (e.length !== 0) for (let t of ["obl", "pay"]) {
			let n = Re.current[t];
			if (!n) continue;
			let r = t === "obl" ? "partner_payable_record" : "partner_payment_record", i = e.find((e) => e.event === r && e.requestId === n);
			if (i) {
				if (i.ok) {
					if (!(t === "obl" ? i.position : (d?.shipments ?? []).find((e) => e.id === (i.shipmentId || p.id))?.finance?.partner?.payments?.some((e) => e.requestId === n))) continue;
					We(t, "", ""), O(""), o(t === "obl" ? "Đã ghi nhận phải trả đối tác" : "Đã ghi nhận thanh toán đối tác", "Backend đã xác nhận ghi sổ — bút toán với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.", "green");
				} else We(t, "", i.error || "Backend từ chối bút toán này."), t === "obl" ? He() : Ue(), o("Chưa ghi nhận được", i.error || "Backend từ chối.", "red");
			}
		}
	}, [d?.lastWrites]);
	let qe = () => {
		let e = N("pxkNo", p?.pxk.number ?? "").trim(), t = N("pxkDate", p?.pxk.date ?? "").trim();
		if (p) {
			if (!e || !t) {
				o("Chưa xuất được PXK", "core.docgen từ chối khi thiếu Số PXK hoặc Ngày PXK — nhập 2 ô ở tab Chứng từ rồi bấm lại.", "red");
				return;
			}
			l("pxk_generate", {
				shipmentId: p.id,
				pxkNo: e,
				pxkDate: t
			}) ? o("Đã gửi yêu cầu xuất PXK " + e, "core.docgen kiểm tra gate giao hàng, sinh file Office thật và lưu metadata chứng từ.", "blue") : o("Không gửi được", "Component chưa kết nối backend.", "red");
		}
	}, Je = () => {
		let e = F({
			delivery_location: N("pxPlace", p.pxk.place || p.importInfo.deliveryAddr || ""),
			receiver_name: N("pxReceiver", p.pxk.receiver || p.importInfo.receiver || ""),
			receiver_title: N("pxRole", p.pxk.role ?? ""),
			delivery_date: N("pxDate", p.importInfo.schedule ?? "")
		});
		if (Object.keys(e).length === 0) {
			o("Chưa có gì để lưu", "Nhập ít nhất một trường người nhận / địa điểm / ngày giao.", "red");
			return;
		}
		l("shipment_field_save", {
			shipmentId: p.id,
			fields: e
		}), ne("Đã lưu thông tin giao nhận " + p.id, ["pxkNo", "pxkDate"]);
	}, Ye = () => {
		let e = p.pxk.document;
		if (!e || !e.downloadBase64) {
			o("File không còn trong phiên này", "Metadata PXK " + (p.pxk.number || p.id) + " vẫn còn trên backend; bytes chỉ được giữ trong phiên đã sinh. Bấm sinh lại để có file tải.", "amber");
			return;
		}
		xo(e.fileName || "PXK_" + (p.pxk.number || p.id) + ".xlsx", e.downloadBase64, e.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
	}, Xe = () => {
		if (!p) return;
		let e = p.importInfo.gnt || {
			payer: "",
			taxCode: "",
			address: ""
		}, t = {
			gnt_taxpayer_name: N("gntPayer", e.payer || ""),
			gnt_taxpayer_tax_code: N("gntTaxCode", e.taxCode || ""),
			gnt_taxpayer_address: N("gntAddress", e.address || "")
		};
		l("shipment_field_save", {
			shipmentId: p.id,
			fields: t
		}) ? o("Đã gửi thông tin Người nộp thuế", "Backend ghi nhận vào hồ sơ hải quan của lô.", "blue") : o("Không gửi được", "Component chưa kết nối backend.", "red");
	}, Ze = () => {
		p && (l("gnt_generate", { shipmentId: p.id }) ? o("Đã gửi yêu cầu tạo Giấy Nộp Thuế", "Hệ thống kiểm tra thông tin tờ khai/thuế và sinh file Excel Mẫu C1-02/NS.", "blue") : o("Không gửi được", "Component chưa kết nối backend.", "red"));
	}, Qe = () => {
		let e = p?.importInfo.gnt?.document;
		if (!e || !e.downloadBase64) {
			o("File không còn trong phiên này", "Bytes chỉ được giữ trong phiên đã sinh. Bấm 'Tạo lại XLSX' để sinh và tải file.", "amber");
			return;
		}
		xo(e.fileName || "GNT_" + p.id + ".xlsx", e.downloadBase64, e.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
	}, $e = (e) => /xe giao|xe TQ|biển số|packing|container|lấy hàng/i.test(e) ? "van-tai" : /tờ khai|thông quan|giao hàng/i.test(e) ? "nhap" : /chứng từ|PXK|HDMB|PL$/i.test(e) ? "chung-tu" : "nhap", et = p.missingDocs.length;
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("button", {
				onClick: () => f(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, R.jsx)(mr, { size: 17 }), " Quay lại"]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [
					/* @__PURE__ */ (0, R.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4 md:p-6",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap items-center gap-2",
								children: [
									/* @__PURE__ */ (0, R.jsx)("h1", {
										className: "text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]",
										children: p.id
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: p.statusTone,
										children: p.status
									}),
									et > 0 && /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "inline-flex items-center gap-1.5 text-[13px] font-bold bg-red-50 text-red-700 border border-red-200 rounded-full px-3 py-1.5",
										children: [
											/* @__PURE__ */ (0, R.jsx)(Wr, { size: 15 }),
											" Thiếu ",
											et,
											" thông tin"
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "ml-auto text-[12.5px] text-slate-400 flex items-center gap-1",
										children: [
											/* @__PURE__ */ (0, R.jsx)(ei, { size: 14 }),
											" Cập nhật ",
											p.updated
										]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-semibold text-[15.5px] mt-1",
								children: [
									p.customer,
									" ",
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "text-slate-400 font-normal",
										children: ["· MST ", p.customerMST]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 mt-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Tuyến",
										value: p.route
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Cửa khẩu",
										value: p.borderVN
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Hợp đồng",
										value: /* @__PURE__ */ (0, R.jsx)(L, {
											to: Yn(p.contract),
											className: "text-[#1e5aa8] font-bold hover:underline",
											children: p.contract
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Sale phụ trách",
										value: /* @__PURE__ */ (0, R.jsx)("span", { children: p.sale })
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Cập nhật bởi",
										value: /* @__PURE__ */ (0, R.jsx)("span", { children: p.support || "—" })
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "px-4 md:px-6 pb-4 md:pb-5",
						children: /* @__PURE__ */ (0, R.jsx)(Do, {
							tone: p.statusTone === "green" ? "green" : p.priority === "Khan" ? "red" : "amber",
							title: p.nextAction,
							desc: p.nextActionDetail,
							action: p.nextLabel,
							onAction: () => {
								if (p.nextRoute.startsWith("/lo-hang")) {
									let e = ms(p.nextRoute);
									n(e ? { tab: e } : {}), document.getElementById("workspace-tabs")?.scrollIntoView({ behavior: "smooth" });
								} else f(p.nextRoute);
							}
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						id: "workspace-tabs",
						className: "px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3",
						children: ds.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => n({ tab: e.id }),
							className: U("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", r === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
							children: [/* @__PURE__ */ (0, R.jsx)("span", {
								className: "hidden md:inline",
								children: e.label
							}), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "md:hidden",
								children: e.short
							})]
						}, e.id))
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				"data-testid": "shipment-header-edit",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "flex items-center justify-between gap-2",
					children: [/* @__PURE__ */ (0, R.jsxs)("button", {
						type: "button",
						onClick: () => b((e) => !e),
						"aria-expanded": y,
						"data-testid": "shipment-header-edit-toggle",
						className: U("btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 px-3.5 min-h-[44px] text-[14px] font-bold", y ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"),
						children: [
							/* @__PURE__ */ (0, R.jsx)(sa, {
								size: 17,
								className: y ? "text-white" : "text-[#1e5aa8]"
							}),
							" Sửa thông tin lô",
							/* @__PURE__ */ (0, R.jsx)(Br, {
								size: 16,
								className: U("transition-transform", y && "rotate-180")
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("span", {
						className: "text-[12.5px] font-semibold text-slate-500 text-right",
						children: [
							"Tên lô = ",
							/* @__PURE__ */ (0, R.jsx)("b", {
								className: "text-[#0f2a4a]",
								children: p.id
							}),
							" · ",
							p.customer,
							!y && /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "hidden md:inline",
								children: [" · tạo ", p.createdAt || "chưa biết"]
							})
						]
					})]
				}), y && /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid gap-3 lg:grid-cols-[1fr_300px] items-start mt-3",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, R.jsx)(jo, {
							label: "Khách hàng của lô",
							testId: "shipment-customer-picker",
							options: c.map((e) => ({
								id: e.id,
								label: e.name || e.id,
								sub: e.mst || e.taxCode ? `MST ${e.mst || e.taxCode} · ${e.id}` : e.id
							})),
							selectedId: k.lotCustomer || p.customerId || "",
							selectedLabel: c.find((e) => e.id === (k.lotCustomer || p.customerId))?.name || p.customer,
							placeholder: "Gõ tên khách hoặc mã khách để tìm…",
							emptyHint: "Danh bạ khách hàng đang trống — thêm khách ở mục Khách Hàng trước.",
							onSelect: (e) => M("lotCustomer", e)
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: ae,
								className: "min-h-[44px] px-4 text-[13.5px]",
								children: "💾 LƯU KHÁCH HÀNG CỦA LÔ"
							}), (k.lotCustomer ?? "") !== "" && (k.lotCustomer ?? "") !== (p.customerId ?? "") && /* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => M("lotCustomer", ""),
								className: "min-h-[44px]",
								children: "Hủy chọn"
							})]
						})]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Ngày tạo lô",
							hint: "DD/MM/YYYY hoặc YYYY-MM-DD · để trống = chưa biết",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								id: "fld-created-at",
								value: N("createdAt", p.createdAt ?? ""),
								onChange: (e) => M("createdAt", e.target.value),
								placeholder: "VD: 03/09/2026",
								className: X()
							})
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: ie,
								className: "min-h-[44px] px-4 text-[13.5px]",
								children: "💾 LƯU NGÀY TẠO"
							}), k.createdAt != null && k.createdAt.trim() === "" && /* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-[12.5px] font-semibold text-amber-700",
								children: "Đang lưu = để trống (chưa biết)"
							})]
						})]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[12.5px] text-slate-500 mt-2.5",
					children: [
						"Mã lô ",
						/* @__PURE__ */ (0, R.jsx)("b", { children: p.id }),
						" là định danh và không đổi ở màn này — đổi mã lô sẽ làm lệch các liên kết hợp đồng đang trỏ vào mã cũ. Ngày tạo là ngày bộ phận vận hành mở lô, không tự suy ra từ ETD/ETA."
					]
				})] })]
			}),
			p.missingDocs.length > 0 && r !== "chung-tu" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-red-200 p-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "font-extrabold text-[15px] text-red-800 flex items-center gap-2 mb-2.5",
					children: [
						/* @__PURE__ */ (0, R.jsx)(Wr, { size: 18 }),
						" Đang thiếu ",
						p.missingDocs.length,
						" thông tin — bấm để bổ sung ngay:"
					]
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "grid gap-2 md:grid-cols-2",
					children: p.missingDocs.map((e) => /* @__PURE__ */ (0, R.jsx)(Oo, {
						what: e,
						actionLabel: "Bổ sung ngay",
						onAction: () => {
							n({ tab: $e(e) }), setTimeout(() => document.getElementById("missing-anchor")?.scrollIntoView({
								behavior: "smooth",
								block: "center"
							}), 150);
						}
					}, e))
				})]
			}),
			r === "van-tai" && /* @__PURE__ */ (0, R.jsx)(ns, {
				shipment: p,
				dispatch: l,
				toast: o
			}),
			r === "lay-hang" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				id: "missing-anchor",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(Yi, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Nhà máy & xuất khẩu"]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-bold text-[15px]",
									children: p.pickup.factory || "Chưa có nhà máy"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13.5px] text-slate-500",
									children: p.pickup.address || "Chưa có địa chỉ lấy hàng"
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[14px] mt-1.5 flex items-center gap-1.5",
									children: [
										/* @__PURE__ */ (0, R.jsx)(da, {
											size: 15,
											className: "text-slate-400"
										}),
										" ",
										p.pickup.contact || "Chưa có liên hệ",
										" · ",
										p.pickup.phone || "—"
									]
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl border border-blue-200 bg-blue-50 p-4 text-[13.5px] text-blue-950",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold",
									children: "Xe/container và lịch chặng được quản lý tại “Vận chuyển & Hàng hóa”."
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1",
									children: "Không nhập biển số TQ và xe giao VN vào cùng một trường."
								}),
								/* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => n({ tab: "van-tai" }),
									className: "touch-target mt-3 rounded-xl bg-[#1e5aa8] text-white font-bold px-4 min-h-[44px]",
									children: "MỞ CÁC CHẶNG VẬN CHUYỂN"
								})
							]
						})
					]
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "space-y-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
								children: ["Xuất khẩu — ", p.exportInfo.border]
							}),
							/* @__PURE__ */ (0, R.jsx)(Ao, {
								label: "Đơn vị khai",
								value: p.exportInfo.declarant
							}),
							/* @__PURE__ */ (0, R.jsx)(Ao, {
								label: "Ngày dự kiến / thực tế",
								value: /* @__PURE__ */ (0, R.jsxs)("span", { children: [
									p.exportInfo.eta || "—",
									" / ",
									p.exportInfo.ata || "chưa có"
								] })
							}),
							/* @__PURE__ */ (0, R.jsx)(Ao, {
								label: "Trạng thái",
								value: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: p.exportInfo.state.includes("Đã") ? "green" : "amber",
									size: "sm",
									children: p.exportInfo.state
								})
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsx)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-1",
								children: "Checklist chứng từ xuất khẩu"
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] text-slate-500 mb-3",
								children: "Hiện trạng → thiếu gì → bấm để bổ sung. Không có cảnh báo cụt."
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "space-y-2",
								children: p.docs.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
									className: U("flex items-center gap-3 rounded-xl border-2 p-3", e.ok ? "border-emerald-200 bg-emerald-50/60" : "border-amber-300 bg-amber-50"),
									children: [
										/* @__PURE__ */ (0, R.jsx)("span", {
											className: U("w-8 h-8 rounded-full grid place-items-center font-extrabold shrink-0", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
											children: e.ok ? "✓" : "!"
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "flex-1 min-w-0",
											children: [/* @__PURE__ */ (0, R.jsxs)("p", {
												className: "font-bold text-[14.5px]",
												children: [
													e.name,
													" — ",
													e.ok ? /* @__PURE__ */ (0, R.jsx)("span", {
														className: "text-emerald-700",
														children: "✅ Đủ"
													}) : /* @__PURE__ */ (0, R.jsx)("span", {
														className: "text-amber-800",
														children: "Thiếu"
													})
												]
											}), e.note && /* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[13px] text-slate-600",
												children: e.note
											})]
										}),
										!e.ok && /* @__PURE__ */ (0, R.jsxs)("button", {
											onClick: () => {
												n({ tab: "chung-tu" }), o("Mở tab Chứng từ", "Tải file " + e.name + " lên hoặc ghi chú lý do thiếu.", "blue");
											},
											className: "btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13.5px] font-bold px-3 min-h-[44px]",
											children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Bổ sung"]
										})
									]
								}, e.name))
							})
						]
					})]
				})]
			}),
			r === "nhap" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				id: "missing-anchor",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "space-y-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
								children: ["Tờ khai & thuế nhập khẩu — ", p.importInfo.borderVN]
							}),
							!N("tk", p.importInfo.declarationNo) && /* @__PURE__ */ (0, R.jsx)(Oo, {
								what: "số tờ khai nhập khẩu",
								where: "Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được",
								actionLabel: "Nhập số TK",
								onAction: () => document.getElementById("fld-tk")?.focus()
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid sm:grid-cols-2 gap-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Số tờ khai",
										required: !p.importInfo.declarationNo,
										error: N("tk", p.importInfo.declarationNo) ? void 0 : "Nhập 12 số tờ khai — VD: 105588421330",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-tk",
											value: N("tk", p.importInfo.declarationNo),
											onChange: (e) => M("tk", e.target.value),
											placeholder: "12 số tờ khai…",
											className: X(N("tk", p.importInfo.declarationNo) ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Ngày đăng ký",
										hint: "Lưu vào ngày tờ khai (2.4.tk_date).",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-tkdate",
											value: N("tkDate", p.importInfo.regDate),
											onChange: (e) => M("tkDate", e.target.value),
											placeholder: "VD: 15/08/2026",
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Thuế nhập khẩu (VND)",
										hint: "Số thực tế trên thông báo thuế/GNT — app không tự tính.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-duty",
											value: N("importDuty", p.importInfo.tax == null ? "" : String(p.importInfo.tax)),
											onChange: (e) => M("importDuty", e.target.value),
											inputMode: "decimal",
											placeholder: "Bỏ trống = chưa biết",
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "VAT hàng nhập (VND)",
										hint: "Số thực tế trên thông báo thuế/GNT — app không tự tính.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-vat",
											value: N("importVat", p.importInfo.vat == null ? "" : String(p.importInfo.vat)),
											onChange: (e) => M("importVat", e.target.value),
											inputMode: "decimal",
											placeholder: "Bỏ trống = chưa biết",
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Phân luồng / kiểm hóa",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: N("inspection", p.importInfo.inspection),
											onChange: (e) => M("inspection", e.target.value),
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Giấy phép chuyên ngành",
										hint: "Chỉ đọc — chưa có trường dữ liệu trong lô.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: p.importInfo.license,
											readOnly: !0,
											placeholder: "Chưa có trường dữ liệu",
											className: X()
										})
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: re,
								className: "w-full",
								children: "💾 LƯU TỜ KHAI & THUẾ"
							}),
							N("tk", p.importInfo.declarationNo) && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13.5px] text-blue-900",
								children: [
									"✅ Đã có số TK ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: N("tk", p.importInfo.declarationNo) }),
									". Tiếp theo: nộp thuế rồi bấm “Thông quan” khi có kết quả phân luồng."
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center justify-between",
								children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
									className: "font-extrabold text-[16px] text-[#0f2a4a] flex items-center gap-2",
									children: [/* @__PURE__ */ (0, R.jsx)(Si, {
										size: 18,
										className: "text-[#1e5aa8]"
									}), " GIẤY NỘP THUẾ (GNT) — Mẫu C1-02/NS"]
								}), p.importInfo.gnt?.done && /* @__PURE__ */ (0, R.jsx)("span", {
									className: "rounded-full bg-emerald-100 text-emerald-800 text-[12px] font-bold px-2.5 py-0.5",
									children: "✅ Đã tạo"
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid sm:grid-cols-2 gap-2 text-[13px]",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "p-2.5 rounded-lg bg-slate-50 border border-slate-200",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-slate-500 block text-[11.5px] font-medium",
											children: "Số tờ khai"
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[#0f2a4a]",
											children: p.importInfo.declarationNo || /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-amber-600 italic font-normal",
												children: "Chưa có"
											})
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "p-2.5 rounded-lg bg-slate-50 border border-slate-200",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-slate-500 block text-[11.5px] font-medium",
											children: "Ngày tờ khai"
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[#0f2a4a]",
											children: p.importInfo.regDate || /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-amber-600 italic font-normal",
												children: "Chưa có"
											})
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "p-2.5 rounded-lg bg-slate-50 border border-slate-200",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-slate-500 block text-[11.5px] font-medium",
											children: "Thuế nhập khẩu"
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[#0f2a4a]",
											children: p.importInfo.tax == null ? /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-amber-600 italic font-normal",
												children: "Chưa có"
											}) : ho(p.importInfo.tax)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "p-2.5 rounded-lg bg-slate-50 border border-slate-200",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-slate-500 block text-[11.5px] font-medium",
											children: "VAT hàng nhập khẩu"
										}), /* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[#0f2a4a]",
											children: p.importInfo.vat == null ? /* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-amber-600 italic font-normal",
												children: "Chưa có"
											}) : ho(p.importInfo.vat)
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-3",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex items-center justify-between",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-bold text-[13.5px] text-[#0f2a4a]",
											children: "Thông tin Người nộp thuế (Pháp nhân chịu thuế)"
										}), p.importInfo.gnt?.customerHint && /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "text-[11.5px] text-slate-500 italic",
											children: ["Gợi ý khách hàng: ", /* @__PURE__ */ (0, R.jsx)("b", { children: p.importInfo.gnt.customerHint })]
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid sm:grid-cols-2 gap-2.5",
										children: [
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Người nộp thuế *",
												hint: "Tên pháp nhân trên tờ khai HQ",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													id: "fld-gnt-payer",
													"data-field": "gnt-payer",
													value: N("gntPayer", p.importInfo.gnt?.payer || ""),
													onChange: (e) => M("gntPayer", e.target.value),
													placeholder: "VD: CÔNG TY TNHH ABC…",
													className: X(N("gntPayer", p.importInfo.gnt?.payer || "") ? "ok" : "missing")
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Mã số thuế (MST) *",
												hint: "MST 10 hoặc 13 số",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													id: "fld-gnt-taxcode",
													"data-field": "gnt-taxcode",
													value: N("gntTaxCode", p.importInfo.gnt?.taxCode || ""),
													onChange: (e) => M("gntTaxCode", e.target.value),
													placeholder: "VD: 0101234567",
													className: X(N("gntTaxCode", p.importInfo.gnt?.taxCode || "") ? "ok" : "missing")
												})
											}),
											/* @__PURE__ */ (0, R.jsx)("div", {
												className: "sm:col-span-2",
												children: /* @__PURE__ */ (0, R.jsx)(Y, {
													label: "Địa chỉ",
													hint: "Địa chỉ trụ sở / đăng ký kinh doanh",
													children: /* @__PURE__ */ (0, R.jsx)("input", {
														id: "fld-gnt-address",
														"data-field": "gnt-address",
														value: N("gntAddress", p.importInfo.gnt?.address || ""),
														onChange: (e) => M("gntAddress", e.target.value),
														placeholder: "Địa chỉ doanh nghiệp nộp thuế…",
														className: X()
													})
												})
											})
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("button", {
										type: "button",
										onClick: Xe,
										className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white font-semibold px-3.5 py-2 text-[13px] hover:bg-[#1e5aa8]",
										children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " LƯU THÔNG TIN NGƯỜI NỘP THUẾ"]
									})
								]
							}),
							p.importInfo.gnt?.noPayable && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-slate-100 border border-slate-300 p-3 text-[13px] text-slate-700",
								children: [
									"ℹ️ ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: "Không có nghĩa vụ thuế:" }),
									" Thuế NK và VAT đều bằng 0 (không cần nộp qua GNT)."
								]
							}),
							p.importInfo.gnt?.missing && p.importInfo.gnt.missing.length > 0 && !p.importInfo.gnt.noPayable && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13px] text-amber-900",
								children: [
									"⚠️ ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: "Chưa đủ điều kiện tạo GNT:" }),
									" Thiếu ",
									p.importInfo.gnt.missing.join(", "),
									". Vui lòng hoàn thiện và lưu ở trên."
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-[12.5px] text-slate-600",
								children: ["ℹ️ ", /* @__PURE__ */ (0, R.jsx)("i", { children: "Cần kiểm tra/hoàn thiện các trường Kho bạc trước khi sử dụng để nộp." })]
							}),
							p.importInfo.gnt?.done && p.importInfo.gnt.document ? /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-emerald-50 border border-emerald-300 p-3.5 space-y-2",
								children: [/* @__PURE__ */ (0, R.jsx)("div", {
									className: "flex items-center justify-between",
									children: /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "font-bold text-emerald-900 text-[14px]",
										children: ["✅ GNT đã tạo: ", p.importInfo.gnt.document.fileName]
									}), /* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[12px] text-emerald-700",
										children: ["Mẫu C1-02/NS (2 sheet) · ", p.importInfo.gnt.document.generatedAt ? new Date(p.importInfo.gnt.document.generatedAt).toLocaleTimeString("vi-VN", {
											hour: "2-digit",
											minute: "2-digit"
										}) : "Vừa tạo"]
									})] })
								}), /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex gap-2 pt-1",
									children: [p.importInfo.gnt.document.downloadAvailable ? /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: Qe,
										className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-4 min-h-[44px] text-[13.5px]",
										children: [/* @__PURE__ */ (0, R.jsx)(ci, { size: 16 }), " TẢI XLSX"]
									}) : /* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] text-emerald-800 self-center",
										children: "Bytes trong phiên trước. Bấm “Tạo lại” để tải."
									}), /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: Ze,
										disabled: !p.importInfo.gnt?.ready,
										className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white font-semibold px-3 min-h-[44px] text-[13px]",
										children: [/* @__PURE__ */ (0, R.jsx)(Si, { size: 15 }), " Tạo lại XLSX"]
									})]
								})]
							}) : /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: Ze,
								disabled: !p.importInfo.gnt?.ready,
								className: U("btn-press touch-target w-full rounded-xl font-bold py-2.5 min-h-[46px] flex items-center justify-center gap-2 text-[14.5px]", p.importInfo.gnt?.ready ? "bg-[#0f2a4a] text-white hover:bg-[#1e5aa8]" : "bg-slate-200 text-slate-400 cursor-not-allowed"),
								children: [/* @__PURE__ */ (0, R.jsx)(Si, { size: 17 }), " TẠO GIẤY NỘP THUẾ XLSX"]
							})
						]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(qa, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Xe Việt Nam & giao hàng"]
						}),
						(!p.importInfo.driverVN || !p.importInfo.plateVN) && !p.importInfo.delivered && /* @__PURE__ */ (0, R.jsx)(Oo, {
							what: "chặng xe giao VN",
							where: "Thêm một chặng Truck riêng; không dùng lại xe lấy hàng TQ",
							actionLabel: "Mở chặng vận chuyển",
							onAction: () => n({ tab: "van-tai" })
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Loại xe VN",
									hint: "Đọc từ xe đầu tiên của chặng Truck giao hàng.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.importInfo.truckVN,
										readOnly: !0,
										placeholder: "Chưa có chặng xe giao",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Biển số VN",
									hint: "Đọc từ chặng Truck giao hàng; sửa tại tab Vận chuyển.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.importInfo.plateVN,
										readOnly: !0,
										placeholder: "Chưa có chặng xe giao",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Tài xế VN",
									hint: "Đọc từ chặng Truck giao hàng; sửa tại tab Vận chuyển.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.importInfo.driverVN,
										readOnly: !0,
										placeholder: "Chưa có tài xế",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Lịch giao",
									hint: "Lưu vào ngày giao (2.7.delivery_date) — PXK cần ngày này.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										id: "fld-schedule",
										value: N("schedule", p.importInfo.schedule),
										onChange: (e) => M("schedule", e.target.value),
										placeholder: "VD: 12/09/2026",
										className: X()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12.5px] font-bold uppercase tracking-wide text-slate-400",
									children: "Địa chỉ giao"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-bold text-[15px] mt-0.5",
									children: p.importInfo.deliveryAddr
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[14px] text-slate-600 mt-1",
									children: [
										"Người nhận: ",
										/* @__PURE__ */ (0, R.jsx)("b", { children: p.importInfo.receiver }),
										" · ",
										p.importInfo.receiverPhone
									]
								}),
								p.importInfo.actualDelivery && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[14px] text-emerald-700 font-bold mt-1",
									children: ["✅ Đã giao: ", p.importInfo.actualDelivery]
								})
							]
						}),
						p.importInfo.delivered ? /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[17px] text-emerald-800",
									children: "✅ ĐÃ GIAO HÀNG XONG"
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[13.5px] text-emerald-700",
									children: [p.importInfo.actualDelivery, " · Sang tab Chứng từ để xuất PXK →"]
								}),
								/* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => n({ tab: "chung-tu" }),
									className: "btn-press touch-target mt-2.5 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]",
									children: ["SANG XUẤT PHIẾU XUẤT KHO ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
								})
							]
						}) : /* @__PURE__ */ (0, R.jsx)(To, {
							onClick: () => v(!0),
							className: "w-full text-[17px] min-h-[56px]",
							children: "✅ XÁC NHẬN ĐÃ GIAO HÀNG"
						})
					]
				})]
			}),
			r === "tai-chinh" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "space-y-4",
				id: "missing-anchor",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("section", {
							className: "rounded-2xl bg-white border-2 border-dashed border-violet-300 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-violet-600 bg-violet-100 inline-block rounded-md px-2 py-0.5",
									children: "Báo giá / Dự kiến — chưa phải số thực thu/chi"
								}),
								/* @__PURE__ */ (0, R.jsx)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2",
									children: "Chi phí dự kiến theo báo giá"
								}),
								p.finance.quote.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[14px] text-slate-500",
									children: ["Chưa gắn báo giá. ", /* @__PURE__ */ (0, R.jsx)(L, {
										to: "/kinh-doanh-bao-gia",
										className: "font-bold text-[#1e5aa8]",
										children: "Mở báo giá →"
									})]
								}),
								p.finance.quote.map((e) => /* @__PURE__ */ (0, R.jsx)(Ao, {
									label: e.label,
									value: /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "font-bold text-[16px]",
										children: [
											W(e.amount, e.ccy),
											" ",
											/* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-[12px] font-bold text-violet-600",
												children: e.ccy
											})
										]
									})
								}, e.label)),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung."
								})
							]
						}), /* @__PURE__ */ (0, R.jsxs)("section", {
							className: "rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-emerald-700 bg-emerald-100 inline-block rounded-md px-2 py-0.5",
									children: "Thực tế — đã phát sinh, có chứng từ"
								}),
								/* @__PURE__ */ (0, R.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mt-2 mb-2",
									children: [
										"Doanh thu & chi phí thực tế (",
										P,
										")"
									]
								}),
								p.finance.actual.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[14px] text-slate-500",
									children: [
										"Chưa ghi nhận dòng thực tế nào — doanh thu / chi phí / lợi nhuận thực tế đang ",
										/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
										", không phải 0."
									]
								}),
								p.finance.actual.length > 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[13.5px] text-slate-500 mb-1",
									children: [
										p.finance.actual.length,
										" dòng dịch vụ đã ghi nhận · tổng hợp theo ",
										P,
										":"
									]
								}),
								/* @__PURE__ */ (0, R.jsx)(Ao, {
									label: "Doanh thu thực tế (chưa VAT)",
									value: /* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-bold",
										children: G(p.finance.receivableNet, P)
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Ao, {
									label: "Chi phí thực tế",
									value: /* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-bold",
										children: G(p.finance.payable, P)
									})
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3",
									children: [
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] font-extrabold uppercase tracking-wider text-emerald-700",
											children: "Lợi nhuận thực tế"
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "grid grid-cols-2 gap-2 mt-1.5 text-center",
											children: [/* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Lãi / Lỗ thực tế"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: U("font-extrabold text-[17px]", p.finance.profit == null ? "text-slate-400" : p.finance.profit < 0 ? "text-red-700" : "text-emerald-700"),
												children: G(p.finance.profit, P)
											})] }), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Biên lợi nhuận"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: U("font-extrabold text-[17px]", p.finance.profitMargin == null ? "text-slate-400" : p.finance.profitMargin < 0 ? "text-red-700" : "text-emerald-700"),
												children: _o(p.finance.profitMargin)
											})] })]
										}),
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12.5px] text-slate-500 mt-2",
											children: "= Doanh thu thực tế − chi phí thực tế − hoa hồng. Không gồm VAT đầu ra. Không lấy số báo giá để bù chỗ trống."
										})
									]
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Chi tiết từng dịch vụ (mã phí · SL · đơn vị · giá vốn · giá bán · VAT · ghi chú) và nút SỬA nằm ở mục “DỊCH VỤ & CHI PHÍ THỰC TẾ” bên dưới."
								})
							]
						})]
					}),
					/* @__PURE__ */ (0, R.jsx)(ss, {
						shipment: p,
						services: u,
						ccy: P,
						dispatch: l,
						toast: o,
						lastWrites: d?.lastWrites
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-1 md:grid-cols-2 gap-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-2",
									children: [
										/* @__PURE__ */ (0, R.jsx)(ro, {
											size: 19,
											className: "text-emerald-600"
										}),
										" Phải thu khách hàng (",
										P,
										")"
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "grid grid-cols-3 gap-2 text-center",
									children: [
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border p-3",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[12px] text-slate-500 font-semibold",
												children: "Phải thu"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px]",
												children: go(p.finance.receivable, P)
											})]
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[12px] text-emerald-700 font-semibold",
												children: "Đã thu"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-emerald-700",
												children: go(p.finance.received, P)
											})]
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-red-50 border border-red-200 p-3",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[12px] text-red-600 font-semibold",
												children: "Còn phải thu"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "font-extrabold text-[16px] md:text-[18px] text-red-700",
												children: go(p.finance.outstanding, P)
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: "Phải thu = doanh thu thực tế + VAT đầu ra. Còn phải thu = phải thu − đã thu, do backend tính."
								}),
								/* @__PURE__ */ (0, R.jsx)("button", {
									onClick: fe,
									className: "btn-press touch-target mt-3 w-full rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
									children: "＋ GHI NHẬN THANH TOÁN"
								})
							]
						}), /* @__PURE__ */ (0, R.jsxs)("section", {
							className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("h3", {
									className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-2",
									children: [
										"Phải trả đối tác (",
										P,
										")"
									]
								}),
								(() => {
									let e = p.finance.partner, t = e?.partnerId ?? "", n = e?.partnerName, r = e?.suggested === !0;
									return /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex flex-wrap items-center gap-2 mb-2",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Đối tác:"
										}), n ? /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "inline-flex items-center gap-1.5 text-[13.5px] font-extrabold text-[#0f2a4a]",
											children: [
												/* @__PURE__ */ (0, R.jsx)(Mr, {
													size: 15,
													className: "text-[#1e5aa8]"
												}),
												" ",
												n,
												/* @__PURE__ */ (0, R.jsx)("span", {
													className: "text-[11.5px] font-bold text-slate-400",
													children: t
												}),
												r && /* @__PURE__ */ (0, R.jsx)("span", {
													className: "text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5",
													children: "đề xuất từ danh mục"
												})
											]
										}) : /* @__PURE__ */ (0, R.jsx)("span", {
											className: "text-[13.5px] font-bold text-slate-400",
											children: "—"
										})]
									}), /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid grid-cols-3 gap-2 text-center",
										children: [
											/* @__PURE__ */ (0, R.jsxs)("div", {
												className: "rounded-xl bg-slate-50 border p-3",
												children: [/* @__PURE__ */ (0, R.jsx)("p", {
													className: "text-[12px] text-slate-500 font-semibold",
													children: "Phải trả"
												}), /* @__PURE__ */ (0, R.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px]",
													children: go(e?.payable ?? null, P)
												})]
											}),
											/* @__PURE__ */ (0, R.jsxs)("div", {
												className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
												children: [/* @__PURE__ */ (0, R.jsx)("p", {
													className: "text-[12px] text-blue-700 font-semibold",
													children: "Đã trả"
												}), /* @__PURE__ */ (0, R.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px] text-blue-700",
													children: go(e?.paid ?? null, P)
												})]
											}),
											/* @__PURE__ */ (0, R.jsxs)("div", {
												className: "rounded-xl bg-amber-50 border border-amber-200 p-3",
												children: [/* @__PURE__ */ (0, R.jsx)("p", {
													className: "text-[12px] text-amber-700 font-semibold",
													children: "Còn phải trả"
												}), /* @__PURE__ */ (0, R.jsx)("p", {
													className: "font-extrabold text-[16px] md:text-[18px] text-amber-800",
													children: go(e?.remaining ?? null, P)
												})]
											})
										]
									})] });
								})(),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] text-slate-400 mt-2",
									children: [
										"Phải trả / đã trả / còn lại đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ) theo lô này. Chưa có sổ ⇒ “—”, không suy ra 0. Đơn vị: ",
										P,
										" — không quy đổi."
									]
								}),
								(p.finance.partner?.payments?.length ?? 0) > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5",
										children: "Lịch sử trả đối tác"
									}), /* @__PURE__ */ (0, R.jsx)("div", {
										className: "space-y-1.5",
										children: p.finance.partner.payments.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
											className: "flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 p-2.5",
											children: [
												/* @__PURE__ */ (0, R.jsx)("span", {
													className: "text-[12px] font-bold text-slate-400 w-[80px]",
													children: e.date || "—"
												}),
												/* @__PURE__ */ (0, R.jsxs)("span", {
													className: "flex-1 min-w-[140px] text-[12.5px] text-slate-600",
													children: [e.note || e.kind, e.requestId ? ` · ${e.requestId}` : ""]
												}),
												/* @__PURE__ */ (0, R.jsxs)("span", {
													className: "font-extrabold text-[14.5px]",
													children: [
														W(e.amount, e.ccy),
														" ",
														/* @__PURE__ */ (0, R.jsx)("span", {
															className: "text-[11px] text-slate-400",
															children: e.ccy
														})
													]
												})
											]
										}, e.id || t))
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-3 rounded-xl border border-slate-200 p-3",
									children: [
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[13px] font-extrabold text-[#0f2a4a] mb-2",
											children: "Ghi nhận phải trả & thanh toán đối tác"
										}),
										/* @__PURE__ */ (0, R.jsx)(Y, {
											label: `Số tiền (${P})`,
											hint: "Ví dụ: 20.000.000 — để trống là UNKNOWN, không tự thành 0",
											children: /* @__PURE__ */ (0, R.jsx)("input", {
												value: D,
												disabled: !!Ie.obl || !!Ie.pay,
												onChange: (e) => {
													O(e.target.value), He(), Ue();
												},
												inputMode: "numeric",
												placeholder: "VD: 20000000",
												className: X()
											})
										}),
										Ie.obl && /* @__PURE__ */ (0, R.jsx)("p", {
											role: "status",
											"data-testid": "partner-payable-pending",
											className: "mt-2 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13px] font-semibold text-blue-800",
											children: "⏳ ĐANG CHỜ BACKEND XÁC NHẬN (phải trả)…"
										}),
										Ie.pay && /* @__PURE__ */ (0, R.jsx)("p", {
											role: "status",
											"data-testid": "partner-payment-pending",
											className: "mt-2 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13px] font-semibold text-blue-800",
											children: "⏳ ĐANG CHỜ BACKEND XÁC NHẬN (thanh toán)…"
										}),
										ze.obl && /* @__PURE__ */ (0, R.jsx)("p", {
											role: "alert",
											className: "mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700",
											children: ze.obl
										}),
										ze.pay && /* @__PURE__ */ (0, R.jsx)("p", {
											role: "alert",
											className: "mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700",
											children: ze.pay
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2.5",
											children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
												onClick: Ge,
												disabled: !!Ie.obl,
												testId: "partner-payable-submit",
												className: "min-h-[48px]",
												children: Ie.obl ? "⏳ ĐANG CHỜ…" : "📌 GHI NHẬN PHẢI TRẢ"
											}), /* @__PURE__ */ (0, R.jsx)(wo, {
												onClick: Ke,
												disabled: !!Ie.pay,
												testId: "partner-payment-submit",
												className: "min-h-[48px]",
												children: Ie.pay ? "⏳ ĐANG CHỜ…" : "💸 TRẢ ĐỐI TÁC"
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, R.jsx)(L, {
									to: "/tai-chinh/doi-soat",
									className: "btn-press touch-target mt-3 w-full rounded-xl border-2 border-slate-200 font-bold min-h-[52px] flex items-center justify-center",
									children: "MỞ ĐỐI SOÁT"
								})
							]
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
							children: "Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa"
						}), /* @__PURE__ */ (0, R.jsx)("div", {
							className: "space-y-2",
							children: p.finance.payments.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
								"data-payment-row": e.id || void 0,
								className: U("flex flex-wrap items-center gap-2 rounded-xl border p-3", e.reversed ? "border-slate-200 bg-slate-50/80" : "border-slate-200"),
								children: [
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-[12.5px] font-bold text-slate-400 w-[92px]",
										children: e.date
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "flex-1 min-w-[160px]",
										children: [/* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block font-bold text-[14.5px]",
											children: [e.kind, e.reversed && /* @__PURE__ */ (0, R.jsx)("span", {
												className: "ml-2 align-middle rounded-full bg-slate-200 text-slate-600 text-[11px] font-extrabold px-2 py-0.5",
												children: "Đã hoàn tác"
											})]
										}), /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "block text-[12.5px] text-slate-500",
											children: [
												e.by,
												e.note ? " · " + e.note : "",
												e.id ? " · " + e.id : ""
											]
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: U("font-extrabold text-[15.5px]", e.reversed && "text-slate-400 line-through"),
										children: [
											W(e.amount, e.ccy),
											" ",
											/* @__PURE__ */ (0, R.jsx)("span", {
												className: "text-[11.5px] text-slate-400",
												children: e.ccy
											})
										]
									}),
									e.reversed ? /* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-[12.5px] font-semibold text-slate-400 px-3",
										children: "Đã điều chỉnh — khóa"
									}) : e.id ? /* @__PURE__ */ (0, R.jsx)("button", {
										onClick: () => je(e),
										className: "touch-target text-[13px] font-bold text-[#1e5aa8] border border-slate-200 rounded-lg px-3 min-h-[40px]",
										"data-payment-id": e.id,
										children: "Điều chỉnh"
									}) : /* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-[12px] font-semibold text-amber-700 px-2",
										title: "Khoản thu legacy không có mã — backend không có đối tượng để liên kết correction.",
										children: "chưa có mã khoản thu"
									})
								]
							}, e.id || t))
						})]
					})
				]
			}),
			r === "chung-tu" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3",
								children: [/* @__PURE__ */ (0, R.jsx)(wi, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Hợp đồng liên kết"]
							}),
							te ? /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl border-2 border-slate-200 p-4",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex flex-wrap items-center gap-2",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-extrabold text-[17px] text-[#0f2a4a]",
											children: te.id
										}), /* @__PURE__ */ (0, R.jsx)(q, {
											tone: te.statusTone,
											size: "sm",
											children: te.status
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[14px] text-slate-600 mt-1",
										children: [
											te.companyLegal,
											" · Giá trị ",
											ho(te.value ?? p.finance.receivable)
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid grid-cols-2 gap-2 mt-3",
										children: [/* @__PURE__ */ (0, R.jsxs)(L, {
											to: Yn(te.id),
											className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] min-h-[48px]",
											children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 16 }), " MỞ HỢP ĐỒNG"]
										}), /* @__PURE__ */ (0, R.jsxs)(L, {
											to: Yn(te.id) + "?tab=chung-tu",
											onClick: () => o("Chứng từ hợp đồng " + te.id, "Mở workdesk chứng từ HDNT/PL/HDMB của hợp đồng (core.docgen).", "blue"),
											className: "btn-press touch-target flex items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] min-h-[48px]",
											children: [/* @__PURE__ */ (0, R.jsx)(vi, { size: 16 }), " MỞ CHỨNG TỪ"]
										})]
									})
								]
							}) : /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-slate-500 text-[14px]",
								children: ["Lô chưa gắn hợp đồng. ", /* @__PURE__ */ (0, R.jsx)(L, {
									to: "/hop-dong",
									className: "font-bold text-[#1e5aa8]",
									children: "Chọn hợp đồng →"
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-4",
								children: [/* @__PURE__ */ (0, R.jsx)("h4", {
									className: "font-bold text-[14.5px] mb-2",
									children: "Chứng từ lô hàng — hiện trạng & bổ sung"
								}), /* @__PURE__ */ (0, R.jsx)("div", {
									className: "space-y-2",
									children: p.docs.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5",
										children: [
											/* @__PURE__ */ (0, R.jsx)("span", {
												className: U("w-7 h-7 rounded-full grid place-items-center text-[13px] font-extrabold", e.ok ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"),
												children: e.ok ? "✓" : "!"
											}),
											/* @__PURE__ */ (0, R.jsxs)("span", {
												className: "flex-1 font-semibold text-[14px]",
												children: [
													e.name,
													" — ",
													e.ok ? /* @__PURE__ */ (0, R.jsx)("span", {
														className: "text-emerald-700",
														children: "Đã đủ"
													}) : /* @__PURE__ */ (0, R.jsx)("span", {
														className: "text-amber-800",
														children: "Thiếu"
													})
												]
											}),
											!e.ok && /* @__PURE__ */ (0, R.jsxs)("button", {
												onClick: () => {
													n({ tab: $e(e.name) }), o("Mở tab bổ sung", "Đi tới ô nhập liệu thật cho " + e.name + ".", "blue");
												},
												className: "btn-press touch-target shrink-0 inline-flex items-center gap-1 rounded-lg bg-amber-500 text-white text-[13px] font-bold px-3 min-h-[44px]",
												children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Bổ sung"]
											})
										]
									}, e.name))
								})]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "rounded-2xl bg-white border-2 border-[#0f2a4a] p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsx)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-1",
								children: "Phiếu xuất kho (PXK) — theo từng lô"
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500 mb-3",
								children: [
									"PXK gắn với lô đã giao, nguồn từ ",
									p.pxk.source || p.contract,
									". Mỗi lô 1 PXK riêng."
								]
							}),
							!p.importInfo.delivered && /* @__PURE__ */ (0, R.jsx)(Oo, {
								what: "xác nhận đã giao hàng",
								where: "Phải giao xong mới được xuất PXK",
								actionLabel: "Sang xác nhận giao",
								onAction: () => n({ tab: "nhap" })
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid sm:grid-cols-2 gap-3 mt-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Số PXK",
										required: !p.pxk.number,
										hint: "Số pháp lý của phiếu — backend không tự đặt.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxkno",
											value: N("pxkNo", p.pxk.number ?? ""),
											onChange: (e) => M("pxkNo", e.target.value),
											placeholder: "VD: PXK-2026-0308",
											className: X(N("pxkNo", p.pxk.number ?? "") ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Ngày PXK",
										required: !p.pxk.date,
										hint: "DD/MM/YYYY hoặc YYYY-MM-DD.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxkdate",
											value: N("pxkDate", p.pxk.date ?? ""),
											onChange: (e) => M("pxkDate", e.target.value),
											placeholder: "VD: 11/09/2026",
											className: X(N("pxkDate", p.pxk.date ?? "") ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Địa điểm nhận",
										required: !p.pxk.place,
										hint: "Lưu vào 2.7.delivery_location — PXK bị chặn nếu thiếu.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxplace",
											value: N("pxPlace", p.pxk.place || p.importInfo.deliveryAddr || ""),
											onChange: (e) => M("pxPlace", e.target.value),
											placeholder: "Kho / địa chỉ nhận thực tế",
											className: X(N("pxPlace", p.pxk.place || p.importInfo.deliveryAddr || "") ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Người nhận",
										required: !p.pxk.receiver,
										hint: "Lưu vào 2.7.receiver_name.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxreceiver",
											value: N("pxReceiver", p.pxk.receiver || p.importInfo.receiver || ""),
											onChange: (e) => M("pxReceiver", e.target.value),
											placeholder: "Tên người nhận",
											className: X(N("pxReceiver", p.pxk.receiver || p.importInfo.receiver || "") ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Chức vụ người nhận",
										required: !p.pxk.role,
										hint: "Lưu vào 2.7.receiver_title.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxrole",
											value: N("pxRole", p.pxk.role ?? ""),
											onChange: (e) => M("pxRole", e.target.value),
											placeholder: "Theo giấy giới thiệu",
											className: X(N("pxRole", p.pxk.role ?? "") ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Ngày giao",
										hint: "Lưu vào 2.7.delivery_date — PXK cần ngày này.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											id: "fld-pxdate",
											value: N("pxDate", p.importInfo.schedule ?? ""),
											onChange: (e) => M("pxDate", e.target.value),
											placeholder: "VD: 12/09/2026",
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Nguồn (HDMB/PL)",
										hint: "Từ hợp đồng đã liên kết với lô — liên kết ở màn Hợp đồng.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: p.pxk.source || p.contract,
											readOnly: !0,
											placeholder: "Chưa liên kết chứng từ nguồn",
											className: X()
										})
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: Je,
								className: "w-full mt-3",
								children: "💾 LƯU THÔNG TIN GIAO NHẬN"
							}),
							(p.pxk.missingDeliveryFacts ?? []).length > 0 && /* @__PURE__ */ (0, R.jsx)(Oo, {
								what: (p.pxk.missingDeliveryFacts ?? []).join(" · "),
								where: "core.docgen chặn PXK đến khi đủ thông tin giao nhận",
								actionLabel: "Nhập ở trên",
								onAction: () => document.getElementById("fld-pxplace")?.focus()
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-3 rounded-xl bg-slate-50 border p-3 text-[13.5px]",
								children: [/* @__PURE__ */ (0, R.jsxs)("p", { children: ["Đã giao hàng xong: ", /* @__PURE__ */ (0, R.jsx)("b", {
									className: p.importInfo.delivered ? "text-emerald-700" : "text-red-600",
									children: p.importInfo.delivered ? "✅ Rồi — " + p.importInfo.actualDelivery : "❌ Chưa"
								})] }), /* @__PURE__ */ (0, R.jsxs)("p", { children: ["Ngày giao: ", /* @__PURE__ */ (0, R.jsx)("b", { children: p.importInfo.actualDelivery || p.importInfo.schedule })] })]
							}),
							p.pxk.done ? /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-3 rounded-xl bg-emerald-50 border-2 border-emerald-300 p-4 text-center",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "font-extrabold text-emerald-800",
										children: ["✅ ĐÃ XUẤT ", p.pxk.number]
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[13.5px] text-emerald-700 mt-0.5",
										children: [
											p.pxk.document?.fileName || "PXK",
											" · bản R",
											p.pxk.document?.revision ?? 1,
											" · ",
											p.pxk.document?.status || "GENERATED",
											p.pxk.document?.generatedBy ? " · " + p.pxk.document.generatedBy : ""
										]
									}),
									p.pxk.document?.downloadAvailable ? /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: Ye,
										className: "btn-press touch-target mt-2 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold px-5 min-h-[48px]",
										children: [
											/* @__PURE__ */ (0, R.jsx)(ci, { size: 17 }),
											" TẢI ",
											p.pxk.document?.fileName || "PXK"
										]
									}) : /* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[13px] text-emerald-800 mt-2",
										children: "File sinh ở phiên trước: metadata còn trên backend, bytes chỉ giữ trong phiên đã sinh — bấm “SINH BẢN MỚI” để có file tải."
									}),
									/* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: qe,
										className: "btn-press touch-target mt-2 ml-2 inline-flex items-center gap-1.5 rounded-xl border-2 border-emerald-600 text-emerald-800 font-bold px-5 min-h-[48px]",
										children: [/* @__PURE__ */ (0, R.jsx)(vi, { size: 17 }), " SINH BẢN MỚI (R+1)"]
									})
								]
							}) : /* @__PURE__ */ (0, R.jsx)(To, {
								onClick: qe,
								className: "w-full mt-3 text-[16px] min-h-[56px]",
								children: "🖨 XUẤT PHIẾU XUẤT KHO"
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsx)(us, {
						shipmentId: p.id,
						attachments: p.attachments ?? [],
						policy: d?.attachmentPolicy
					})
				]
			}),
			r === "lich-su" && /* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 max-w-[800px]",
				children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
					className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-4",
					children: ["Dòng thời gian — ", p.id]
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200",
					children: p.timeline.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "relative",
						children: [
							/* @__PURE__ */ (0, R.jsx)("span", { className: U("absolute -left-6 top-1 w-4 h-4 rounded-full border-[3px] border-white shadow", e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : e.tone === "red" ? "bg-red-500" : "bg-blue-500") }),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12.5px] font-bold text-slate-400",
								children: e.time
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-bold text-[15px] text-[#0f2a4a]",
								children: e.title
							}),
							e.desc && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13.5px] text-slate-600",
								children: e.desc
							})
						]
					}, t))
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "xl:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: [
					r === "nhap" && !p.importInfo.delivered && /* @__PURE__ */ (0, R.jsx)("button", {
						onClick: () => v(!0),
						className: "btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
						children: "✅ XÁC NHẬN ĐÃ GIAO"
					}),
					r === "chung-tu" && /* @__PURE__ */ (0, R.jsx)("button", {
						onClick: qe,
						className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]",
						children: "🖨 XUẤT PHIẾU XUẤT KHO"
					}),
					r === "tai-chinh" && /* @__PURE__ */ (0, R.jsx)("button", {
						onClick: fe,
						className: "btn-press touch-target flex-1 rounded-xl bg-emerald-600 text-white font-extrabold min-h-[52px]",
						children: "＋ GHI NHẬN THANH TOÁN"
					})
				]
			}),
			g && /* @__PURE__ */ (0, R.jsxs)(ko, {
				id: "delivery-confirm-sheet",
				testId: "delivery-confirm-sheet",
				labelledBy: "delivery-sheet-title",
				width: 480,
				onClose: () => v(!1),
				children: [
					/* @__PURE__ */ (0, R.jsxs)("h3", {
						id: "delivery-sheet-title",
						className: "font-extrabold text-[18px] text-[#0f2a4a]",
						children: [
							"Xác nhận đã giao ",
							p.id,
							"?"
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14.5px] text-slate-600 mt-1.5",
						children: [
							"Khách ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: p.customer }),
							" đã ký nhận đủ ",
							/* @__PURE__ */ (0, R.jsxs)("b", { children: [p.cargo.packs, " kiện"] }),
							" tại ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: p.importInfo.deliveryAddr }),
							"? Sau xác nhận, lô chuyển sang “Đã giao” và mở được PXK."
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: () => v(!1),
							children: "Chưa, để sau"
						}), /* @__PURE__ */ (0, R.jsx)(To, {
							onClick: oe,
							children: "✅ ĐÃ GIAO"
						})]
					})
				]
			}),
			m && /* @__PURE__ */ (0, R.jsxs)(ko, {
				id: "payment-record-sheet",
				testId: "payment-record-sheet",
				labelledBy: "payment-sheet-title",
				pending: !!se,
				width: 480,
				onClose: () => h(!1),
				children: [
					/* @__PURE__ */ (0, R.jsxs)("h3", {
						id: "payment-sheet-title",
						className: "font-extrabold text-[18px] text-[#0f2a4a]",
						children: ["Ghi nhận thanh toán — ", p.id]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500",
						children: ["Còn phải thu: ", /* @__PURE__ */ (0, R.jsx)("b", {
							className: "text-red-700",
							children: G(p.finance.outstanding, P)
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Loại khoản",
							children: /* @__PURE__ */ (0, R.jsxs)("select", {
								value: T,
								disabled: !!se,
								onChange: (e) => {
									E(e.target.value), I.current = ps("PAY");
								},
								className: X(),
								children: [
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu tiền khách" }),
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu tạm ứng" }),
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu nốt công nợ" }),
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Trả đối tác" })
								]
							})
						}), /* @__PURE__ */ (0, R.jsx)(Y, {
							label: `Số tiền (${P})`,
							required: !0,
							error: x ? void 0 : "Nhập số tiền — VD: 150000000",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: x,
								disabled: !!se,
								onChange: (e) => {
									w(e.target.value), I.current = ps("PAY");
								},
								inputMode: "numeric",
								placeholder: "VD: 150000000",
								className: X(x ? "ok" : "missing")
							})
						})]
					}),
					se ? /* @__PURE__ */ (0, R.jsx)("p", {
						role: "status",
						"data-testid": "payment-record-pending",
						className: "mt-2.5 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13.5px] font-semibold text-blue-800",
						children: "⏳ ĐANG CHỜ BACKEND XÁC NHẬN… Không gửi lại và không đóng trang."
					}) : /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-2",
						children: [
							"Ghi theo đồng tiền của lô (",
							P,
							") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai."
						]
					}),
					ue && /* @__PURE__ */ (0, R.jsx)("p", {
						role: "alert",
						id: "payment-record-error",
						className: "mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700",
						children: ue
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-2",
						children: ["Mã yêu cầu: ", /* @__PURE__ */ (0, R.jsx)("b", {
							className: "font-mono",
							children: I.current
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: () => h(!1),
							disabled: !!se,
							children: "Hủy"
						}), /* @__PURE__ */ (0, R.jsx)(To, {
							onClick: me,
							disabled: !!se,
							testId: "payment-record-submit",
							children: se ? "⏳ ĐANG CHỜ BACKEND XÁC NHẬN…" : "💾 LƯU KHOẢN THU"
						})]
					})
				]
			}),
			he && /* @__PURE__ */ (0, R.jsxs)(ko, {
				id: "payment-correction-sheet",
				testId: "payment-correction-sheet",
				labelledBy: "correction-sheet-title",
				pending: !!De,
				width: 520,
				onClose: Me,
				children: [
					/* @__PURE__ */ (0, R.jsx)("h3", {
						id: "correction-sheet-title",
						className: "font-extrabold text-[18px] text-[#0f2a4a]",
						children: "Điều chỉnh khoản thu — hoàn tác có kiểm toán"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[13px] text-slate-500 mt-0.5",
						children: "Khoản thu gốc không bị sửa nội dung và không bị xóa: backend ghi một correction liên kết (financial_corrections + audit payment_reversed) rồi đánh dấu khoản thu “Đã hoàn tác”. Số dư phải thu đọc lại từ backend — không phải từ màn hình này."
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border border-slate-200 bg-slate-50 p-3 mt-3 grid grid-cols-[110px_1fr] gap-x-3 gap-y-1.5 text-[13px]",
						id: "correction-original-facts",
						children: [
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-slate-400 font-bold",
								children: "Payment ID"
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "font-bold text-slate-700 break-all text-right",
								children: he.id
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-slate-400 font-bold",
								children: "Ngày"
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "font-bold text-slate-700 text-right",
								children: he.date || "—"
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-slate-400 font-bold",
								children: "Số tiền"
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "font-extrabold text-slate-700 text-right",
								children: W(he.amount, he.ccy)
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-slate-400 font-bold",
								children: "Loại"
							}),
							/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "font-bold text-slate-700 text-right",
								children: [he.kind, he.note && he.note !== he.kind ? " · " + he.note : ""]
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-slate-400 font-bold",
								children: "Đồng tiền"
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "font-bold text-slate-700 text-right",
								children: he.ccy
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Lý do điều chỉnh",
							required: !0,
							error: Te && !_e.trim() ? Te : void 0,
							hint: "Bắt buộc — backend từ chối correction không có lý do.",
							children: /* @__PURE__ */ (0, R.jsx)("textarea", {
								value: _e,
								onChange: (e) => ve(e.target.value),
								disabled: !!De,
								rows: 2,
								placeholder: "VD: Khách chuyển khoản sai nội dung — hoàn tác khoản này, khoản ghi lại sẽ nhập riêng.",
								className: X(_e.trim() ? "ok" : "missing")
							})
						}), /* @__PURE__ */ (0, R.jsxs)("details", {
							className: "rounded-xl border border-slate-200 p-3",
							children: [/* @__PURE__ */ (0, R.jsx)("summary", {
								className: "cursor-pointer text-[13.5px] font-bold text-slate-600",
								children: "Bằng chứng kèm theo (không bắt buộc — KHÔNG phải số tiền thay thế)"
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid gap-3 mt-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: `Số tiền liên quan (${he.ccy || P})`,
										error: Te && ye.trim() && yo(ye) == null ? Te : void 0,
										hint: "Chỉ lưu kèm correction làm bằng chứng. Để trống = không nhập, không tự thành 0.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: ye,
											onChange: (e) => be(e.target.value),
											disabled: !!De,
											inputMode: "decimal",
											placeholder: "VD: 1.200.000",
											className: X(ye.trim() && yo(ye) == null ? "invalid" : "ok")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Ngày liên quan",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: xe,
											onChange: (e) => Se(e.target.value),
											disabled: !!De,
											placeholder: "VD: 11/09/2026",
											className: X("ok")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Ghi chú",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: Ce,
											onChange: (e) => we(e.target.value),
											disabled: !!De,
											placeholder: "Chứng từ, ủy nhiệm chi, email khách…",
											className: X("ok")
										})
									})
								]
							})]
						})]
					}),
					Te && _e.trim() && /* @__PURE__ */ (0, R.jsx)("p", {
						className: "mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700",
						role: "alert",
						id: "correction-backend-error",
						children: Te
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-2",
						children: [
							"Mã yêu cầu: ",
							/* @__PURE__ */ (0, R.jsx)("b", {
								className: "font-mono",
								children: ke.current
							}),
							" — bấm lặp lại cùng ý định này không tạo correction thứ hai; đóng rồi mở lại là ý định mới với mã mới."
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: Me,
							children: De ? "Đang chờ backend…" : "Hủy"
						}), /* @__PURE__ */ (0, R.jsx)(wo, {
							onClick: Ne,
							disabled: !!De,
							children: De ? "⏳ ĐANG GHI…" : "✅ XÁC NHẬN ĐIỀU CHỈNH / HOÀN TÁC"
						})]
					})
				]
			}),
			ee > 0 && /* @__PURE__ */ (0, R.jsx)("span", { className: "hidden" })
		]
	});
}
//#endregion
//#region src/pages/CreateShipment.tsx
function gs() {
	let { customers: e, quotes: t, contracts: n, dispatch: r, toast: i } = Jn(), a = yt(), o = (0, _.useSyncExternalStore)(C, S, S), [s, c] = (0, _.useState)(""), [l, u] = (0, _.useState)(""), [d, f] = (0, _.useState)(""), [p, m] = (0, _.useState)(""), [h, g] = (0, _.useState)(""), [v, y] = (0, _.useState)("DAP"), [b, x] = (0, _.useState)(""), [w, T] = (0, _.useState)(""), [E, D] = (0, _.useState)(null), [O, k] = (0, _.useState)(""), A = (0, _.useMemo)(() => t.filter((e) => (e.status || "").toLowerCase().includes("accept") || (e.status || "").toLowerCase().includes("chốt")), [t]), ee = t.find((e) => e.id === s) ?? null, j = (r) => {
		c(r);
		let a = t.find((e) => e.id === r);
		if (!a) return;
		let o = e.find((e) => e.id === a.customerId) ?? e.find((e) => e.name === a.customer);
		o && f(o.id), g([
			"Truck",
			"Sea",
			"Air",
			"Rail"
		].includes(a.transportMode) ? a.transportMode : ""), y(a.incoterm || "DAP"), x(a.origin || ""), T(a.destination || "");
		let s = a.customerId ? n.filter((e) => e.customerId === a.customerId) : [];
		if (s.length === 1) {
			m(s[0].id), i("Đã nạp báo giá " + r, "Khách hàng + hợp đồng " + s[0].id + " đã điền sẵn từ báo giá đã chốt.", "blue");
			return;
		}
		if (s.length > 1) {
			m(""), i("Đã nạp báo giá " + r, `Khách ${a.customer} có ${s.length} hợp đồng — chọn đúng hợp đồng ở ô “Hợp đồng liên kết”.`, "amber");
			return;
		}
		i("Đã nạp báo giá " + r, "Giá trị và khách hàng đã được điền sẵn từ báo giá đã chốt.", "blue");
	};
	return (0, _.useEffect)(() => {
		if (!E || !o) return;
		let e = (o.lastWrites ?? []).find((e) => e.event === "shipment_create" && e.requestId === E.requestId);
		e && (e.ok ? (o.shipments ?? []).some((e) => e.id === E.shipmentId) ? (D(null), i("Đã tạo lô " + E.shipmentId, "Backend ghi + audit thành công; lô đã có trong dữ liệu mới.", "green"), a(`/lo-hang/${E.shipmentId}?tab=van-tai`)) : (D(null), k("Backend báo thành công nhưng lô chưa xuất hiện trong dữ liệu mới — chưa chuyển màn hình.")) : (D(null), k(e.error || "Backend từ chối yêu cầu tạo lô."), i("Không tạo được lô", e.error || "Backend từ chối.", "red")));
	}, [
		o,
		E,
		a,
		i
	]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1000px]",
		children: [/* @__PURE__ */ (0, R.jsxs)(L, {
			to: "/lo-hang",
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, R.jsx)(mr, { size: 17 }), " Về danh sách lô"]
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
			children: [/* @__PURE__ */ (0, R.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }), /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "p-4 md:p-6",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						title: "Tạo Lô Hàng Mới",
						sub: "Bắt đầu từ báo giá đã chốt để tự điền, rồi chỉ bổ sung phần còn thiếu. Ghi bằng writer hiện có của Logistics."
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-2xl bg-blue-50 border border-blue-200 p-4 mb-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-extrabold text-[15px] text-blue-900 flex items-center gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)(La, { size: 17 }), " 1 · Chọn báo giá đã chốt (không bắt buộc)"]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3",
								children: [A.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[14px] text-blue-800",
									children: "Chưa có báo giá đã chốt trong dữ liệu hiện tại — có thể nhập tay bên dưới."
								}), A.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => j(e.id),
									className: U("touch-target text-left rounded-xl border-2 bg-white p-3.5 lift", s === e.id ? "border-[#1e5aa8]" : "border-slate-200"),
									children: [
										/* @__PURE__ */ (0, R.jsxs)("p", {
											className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-1.5",
											children: [
												/* @__PURE__ */ (0, R.jsx)(gi, {
													size: 16,
													className: "text-emerald-600"
												}),
												" ",
												e.id
											]
										}),
										/* @__PURE__ */ (0, R.jsxs)("p", {
											className: "text-[13.5px] text-slate-600 mt-0.5",
											children: [
												e.customer,
												" · ",
												K(e.status)
											]
										}),
										/* @__PURE__ */ (0, R.jsxs)("p", {
											className: "text-[13.5px] font-bold text-[#1e5aa8] mt-1",
											children: [
												W(e.total),
												" ",
												e.currency ?? "VND"
											]
										})
									]
								}, e.id))]
							}),
							ee && /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13.5px] text-blue-900 mt-3",
								children: [
									"Đã chọn ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: ee.id }),
									" — Quote Estimate chỉ dùng để điền trước; Finance Actual sẽ nhập riêng ở tab Tài chính của lô."
								]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-2xl border-2 border-slate-200 p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)(ra, { size: 17 }), " 2 · Thông tin lô"]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Mã lô (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: l,
											onChange: (e) => u(e.target.value.toUpperCase()),
											placeholder: "LO-0470",
											className: X(l.trim() ? "ok" : "missing")
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Khách hàng (bắt buộc)",
										required: !0,
										children: /* @__PURE__ */ (0, R.jsxs)("select", {
											value: d,
											onChange: (e) => f(e.target.value),
											className: X(d ? "ok" : "missing"),
											children: [/* @__PURE__ */ (0, R.jsx)("option", {
												value: "",
												children: "-- Chọn khách hàng --"
											}), e.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
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
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Hợp đồng liên kết",
										hint: "PXK/chứng từ của lô lấy nguồn từ hợp đồng này; sau khi tạo lô thì không đổi được ở màn lô.",
										children: /* @__PURE__ */ (0, R.jsxs)("select", {
											value: p,
											onChange: (e) => m(e.target.value),
											className: X(),
											children: [/* @__PURE__ */ (0, R.jsx)("option", {
												value: "",
												children: "-- Chưa liên kết --"
											}), n.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
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
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Mode đầu tiên (không bắt buộc) / Incoterm",
										hint: "Chọn mode để tạo chặng đầu; xe/container bổ sung sau ở chi tiết lô.",
										children: /* @__PURE__ */ (0, R.jsxs)("div", {
											className: "flex gap-2",
											children: [/* @__PURE__ */ (0, R.jsxs)("select", {
												value: h,
												onChange: (e) => g(e.target.value),
												className: X(),
												children: [/* @__PURE__ */ (0, R.jsx)("option", {
													value: "",
													children: "-- Bổ sung sau --"
												}), [
													"Truck",
													"Sea",
													"Air",
													"Rail"
												].map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
													value: e,
													children: e
												}, e))]
											}), /* @__PURE__ */ (0, R.jsx)("select", {
												value: v,
												onChange: (e) => y(e.target.value),
												className: X(),
												children: [
													"EXW",
													"FCA",
													"FOB",
													"CIF",
													"DAP",
													"DDP"
												].map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
													value: e,
													children: e
												}, e))
											})]
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Nơi đi cơ bản",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: b,
											onChange: (e) => x(e.target.value),
											placeholder: "Bằng Tường (Quảng Tây)",
											className: X()
										})
									}),
									/* @__PURE__ */ (0, R.jsx)(Y, {
										label: "Nơi đến cơ bản",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: w,
											onChange: (e) => T(e.target.value),
											placeholder: "Hữu Nghị (Lạng Sơn)",
											className: X()
										})
									})
								]
							}),
							O && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5",
								role: "alert",
								children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
									size: 18,
									className: "text-red-600 shrink-0 mt-0.5"
								}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[14.5px] text-red-800",
									children: "Backend từ chối — lô chưa được tạo"
								}), /* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13.5px] text-red-700 mt-0.5 break-words",
									children: O
								})] })]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-col sm:flex-row gap-2.5 mt-4",
								children: [/* @__PURE__ */ (0, R.jsx)(wo, {
									onClick: () => {
										if (E) return;
										if (!l.trim()) {
											i("Thiếu mã lô", "Nhập mã lô (ví dụ LO-0470) rồi bấm Tạo lô hàng.", "red");
											return;
										}
										if (!d.trim()) {
											i("Thiếu khách hàng", "Chọn khách hàng — backend từ chối lô không có khách.", "red");
											return;
										}
										if (!h && (b.trim() || w.trim())) {
											i("Thiếu mode đầu tiên", "Chọn mode hoặc để trống cả nơi đi/đến để bổ sung sau.", "red");
											return;
										}
										let t = l.trim().toUpperCase(), n = `create-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
										r("shipment_create", {
											shipmentId: t,
											customerId: e.find((e) => e.id === d)?.id ?? "",
											customer: e.find((e) => e.id === d)?.name ?? "",
											contractId: p.trim(),
											currency: "VND",
											transport: {
												mode: h,
												incoterm: v,
												pol: b.trim(),
												pod: w.trim()
											},
											requestId: n
										}) ? (k(""), D({
											shipmentId: t,
											requestId: n
										}), i("Đã gửi yêu cầu tạo " + t, "Đang lưu và xác nhận lô hàng…", "blue")) : i("Không gửi được", "Component chưa kết nối backend.", "red");
									},
									disabled: !!E,
									className: "flex-1",
									children: E ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: ["TẠO LÔ HÀNG ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })] })
								}), /* @__PURE__ */ (0, R.jsx)(L, {
									to: "/lo-hang",
									className: "btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px]",
									children: "Hủy"
								})]
							}),
							E && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] font-semibold text-blue-700 mt-2.5",
								children: "Đang lưu và xác nhận lô hàng…"
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500 mt-3",
								children: [
									"Lô được ghi qua writer hiện có của Logistics, có audit. Mã lô trùng sẽ bị từ chối. Các trường để trống được giữ là ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: "không xác định" }),
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
function _s() {
	let { shipments: e } = Jn(), [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(""), a = (0, _.useMemo)(() => e.filter((e) => !r || (e.id + e.customer + (e.transport?.containerNo ?? "")).toLowerCase().includes(r.toLowerCase())), [e, r]), o = e.find((e) => e.id === t) ?? a[0] ?? null, s = o?.tracking ?? null;
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
			children: [/* @__PURE__ */ (0, R.jsx)(J, {
				title: "Theo Dõi Vận Chuyển",
				sub: "Hiện trạng và mốc vận chuyển có thật từ dữ liệu lô hàng. Không mô phỏng vị trí GPS."
			}), /* @__PURE__ */ (0, R.jsx)("input", {
				value: r,
				onChange: (e) => i(e.target.value),
				placeholder: "Lọc theo mã lô, khách, biển số / container…",
				className: "w-full rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] focus:border-[#1e5aa8] outline-none"
			})]
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4",
			children: [/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "p-3.5 border-b border-slate-200",
					children: /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "font-extrabold text-[15px] text-[#0f2a4a]",
						children: [
							"Lô hàng (",
							a.length,
							")"
						]
					})
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "divide-y divide-slate-100 max-h-[620px] overflow-y-auto",
					children: [a.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
						className: "p-6 text-center text-slate-500 text-[14px]",
						children: "Không có lô nào khớp."
					}), a.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
						onClick: () => n(e.id),
						className: U("touch-target w-full text-left p-3.5 hover:bg-slate-50", o?.id === e.id ? "bg-blue-50" : ""),
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Co, { tone: e.statusTone }),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-extrabold text-[15px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: e.statusTone,
										size: "sm",
										children: e.status
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13.5px] text-slate-600 mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12.5px] text-slate-400 mt-0.5 truncate",
								children: K(e.route)
							})
						]
					}, e.id))]
				})]
			}), /* @__PURE__ */ (0, R.jsx)("div", {
				className: "space-y-4",
				children: !o || !s ? /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-10 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-extrabold text-[18px]",
						children: "Chọn một lô để xem hành trình"
					}), /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-slate-500 mt-1 text-[14.5px]",
						children: "Dữ liệu theo dõi lấy trực tiếp từ trạng thái vận chuyển của lô."
					})]
				}) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [
								/* @__PURE__ */ (0, R.jsx)(qa, {
									size: 20,
									className: "text-[#1e5aa8]"
								}),
								/* @__PURE__ */ (0, R.jsxs)("h2", {
									className: "font-extrabold text-[19px] text-[#0f2a4a]",
									children: [
										o.id,
										" · ",
										o.customer
									]
								}),
								/* @__PURE__ */ (0, R.jsx)(q, {
									tone: s.statusTone,
									children: s.status
								}),
								/* @__PURE__ */ (0, R.jsx)(L, {
									to: `/lo-hang/${o.id}`,
									className: "ml-auto btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px]",
									children: "Mở 360°"
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Hãng vận chuyển"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[15px] text-[#0f2a4a] mt-0.5",
										children: K(s.carrier)
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Mã vận đơn / xe"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[15px] text-[#0f2a4a] mt-0.5",
										children: K(s.reference)
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3.5",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] font-semibold text-slate-500",
										children: "Tra cứu hãng"
									}), s.trackingUrl ? /* @__PURE__ */ (0, R.jsxs)("a", {
										href: s.trackingUrl,
										target: "_blank",
										rel: "noreferrer",
										className: "inline-flex items-center gap-1.5 font-extrabold text-[14.5px] text-[#1e5aa8] mt-0.5",
										children: ["Mở trang hãng ", /* @__PURE__ */ (0, R.jsx)(fi, { size: 15 })]
									}) : /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[15px] text-slate-400 mt-0.5",
										children: "—"
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 flex items-start gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(Yi, {
								size: 17,
								className: "text-amber-700 mt-0.5 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13.5px] text-amber-900",
								children: s.positionNote
							})]
						})
					]
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center gap-2 mb-3",
							children: [/* @__PURE__ */ (0, R.jsx)(ta, {
								size: 19,
								className: "text-[#0f2a4a]"
							}), /* @__PURE__ */ (0, R.jsx)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a]",
								children: "Mốc vận chuyển"
							})]
						}),
						s.milestones.length === 0 && /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500",
							children: "Chưa có mốc nào được ghi nhận cho lô này."
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "relative pl-6",
							children: [/* @__PURE__ */ (0, R.jsx)("span", { className: "absolute left-[9px] top-2 bottom-2 w-0.5 bg-slate-200" }), /* @__PURE__ */ (0, R.jsx)("div", {
								className: "space-y-3",
								children: s.milestones.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "relative",
									children: [/* @__PURE__ */ (0, R.jsx)("span", { className: U("absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white", e.done ? e.tone === "green" ? "bg-emerald-500" : e.tone === "amber" ? "bg-amber-500" : "bg-blue-500" : "bg-slate-300") }), /* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl border border-slate-200 p-3.5",
										children: [/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "flex flex-wrap items-center gap-2",
											children: [
												/* @__PURE__ */ (0, R.jsx)("p", {
													className: "font-extrabold text-[15px] text-[#0f2a4a]",
													children: e.title
												}),
												/* @__PURE__ */ (0, R.jsx)("span", {
													className: "text-[13px] font-bold text-slate-500",
													children: K(e.time)
												}),
												/* @__PURE__ */ (0, R.jsx)(q, {
													tone: e.done ? e.tone : "gray",
													size: "sm",
													children: e.done ? "Đã diễn ra" : "Chưa"
												})
											]
										}), e.desc && /* @__PURE__ */ (0, R.jsx)("p", {
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
function vs() {
	let { receivables: e, dispatch: t, toast: n } = Jn(), r = (0, _.useSyncExternalStore)(C, S, S), [i] = Rn(), [a, o] = Ro("q"), [s, c] = (0, _.useState)(() => [
		"noPaid",
		"ccy",
		"sale",
		"support",
		"status"
	].some((e) => i.get(e))), [l, u] = zo("noPaid"), [d, f] = Ro("ccy"), p = d || "ALL", m = (e) => f(e === "ALL" ? "" : e), [h, g] = Ro("sale"), v = h || "ALL", y = (e) => g(e === "ALL" ? "" : e), [b, x] = Ro("support"), w = b || "ALL", T = (e) => x(e === "ALL" ? "" : e), [E, D] = Ro("status"), O = E || "ALL", k = (e) => D(e === "ALL" ? "" : e), [A, ee] = (0, _.useState)(null), [j, M] = (0, _.useState)(""), [N, te] = (0, _.useState)("Thu tiền khách"), P = (0, _.useRef)(""), [F, ne] = (0, _.useState)(""), re = (0, _.useRef)(""), [ie, ae] = (0, _.useState)(""), oe = e.rows ?? [], I = e.totals ?? {}, se = ["ALL", ...Array.from(new Set(oe.map((e) => e.currency)))], ce = ["ALL", ...Array.from(new Set(oe.map((e) => e.sale).filter((e) => e)))], le = ["ALL", ...Array.from(new Set(oe.map((e) => e.support).filter((e) => e)))], ue = ["ALL", ...Array.from(new Set(oe.map((e) => e.status)))], de = (0, _.useMemo)(() => {
		let e = a.trim().toLowerCase();
		return oe.filter((t) => !(l && !(t.outstanding != null && t.outstanding > 0) || p !== "ALL" && t.currency !== p || v !== "ALL" && (t.sale || "") !== v || w !== "ALL" && (t.support || "") !== w || O !== "ALL" && t.status !== O || e && !(t.id + " " + t.customer + " " + (t.sale || "") + " " + (t.support || "")).toLowerCase().includes(e))).sort((e, t) => (t.outstanding ?? -1) - (e.outstanding ?? -1));
	}, [
		oe,
		a,
		l,
		p,
		v,
		w,
		O
	]), fe = (e) => {
		P.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, re.current = "", ne(""), ae(""), M(""), te("Thu tiền khách"), ee(e);
	};
	return (0, _.useEffect)(() => {
		if (!F) return;
		let e = (r?.lastWrites ?? []).find((e) => e.event === "payment_record" && e.requestId === F);
		if (e) {
			if (e.ok) {
				if (!(r?.shipments ?? []).find((e) => e.id === A?.id)?.finance?.payments?.some((e) => e.requestId === F)) return;
				ee(null), M(""), ae(""), re.current = "", ne(""), n("Đã ghi nhận khoản thu", "Backend đã xác nhận ghi sổ — khoản thu với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.", "green");
			} else re.current = "", ne(""), ae(e.error || "Backend từ chối khoản thu này."), P.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, n("Chưa ghi nhận được", e.error || "Backend từ chối khoản thu.", "red");
		}
	}, [r?.lastWrites, F]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(ro, {
							size: 20,
							className: "text-emerald-600"
						}),
						title: "Thu tiền khách · Phải thu",
						sub: "Toàn bộ phải thu khách hàng theo lô — đọc từ sổ tài chính thật (core.logic). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [Object.keys(I).length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có lô nào chốt dòng thực tế — phải thu đang ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
								", không phải 0."
							]
						}), Object.entries(I).map(([e, t]) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 mb-2",
								children: [/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500",
									children: ["Tổng phải thu · ", e]
								}), /* @__PURE__ */ (0, R.jsx)("span", {
									className: "text-[11px] text-slate-400",
									children: "không quy đổi sang đồng tiền khác"
								})]
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 text-center",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-white border p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Phải thu"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]",
											children: G(t.receivable, e)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-emerald-50 border border-emerald-200 p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-emerald-700 font-semibold",
											children: "Đã thu"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-emerald-700",
											children: G(t.received, e)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-red-50 border border-red-200 p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-red-600 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-red-700",
											children: G(t.outstanding, e)
										})]
									})
								]
							})]
						}, e))]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex gap-2 mt-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: a,
								onChange: (e) => o(e.target.value),
								placeholder: "Tìm mã lô (LO-0306), khách (An Phát), Sale, Support…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => c((e) => !e),
							className: U("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, R.jsx)(Fa, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					s && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => u(!l),
								className: U("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", l ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600"),
								children: [/* @__PURE__ */ (0, R.jsx)(Wr, { size: 16 }), " Chỉ lô còn phải thu"]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đồng tiền:"
								}), se.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => m(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", p === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Sale:"
								}), ce.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => y(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", v === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : K(e)
								}, e))]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Support:"
								}), le.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => T(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", w === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : K(e)
								}, e))]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Trạng thái:"
								}), ue.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => k(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", O === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [de.length, " lô"]
							}),
							" · Ưu tiên theo còn phải thu thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: /* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[1080px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Lô" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Phải thu" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Đã thu" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Còn lại" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Đồng tiền" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Sale · Support" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: de.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(L, {
									to: "/lo-hang/" + e.id + "?tab=tai-chinh",
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: K(e.customer)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold",
									children: G(e.receivable, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "text-emerald-700 font-semibold",
									children: G(e.received, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: U("font-extrabold", !mo(e.outstanding) && (e.outstanding ?? 0) > 0 ? "text-red-700" : "text-slate-500"),
									children: G(e.outstanding, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("span", {
									className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
									children: e.currency
								}) }),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Sale: ", /* @__PURE__ */ (0, R.jsx)("b", { children: K(e.sale) })]
									}), /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "block whitespace-nowrap",
										children: ["Cập nhật bởi: ", /* @__PURE__ */ (0, R.jsx)("b", { children: K(e.support) })]
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.statusTone,
									size: "sm",
									children: K(e.status)
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, R.jsxs)(L, {
										to: "/lo-hang/" + e.id + "?tab=tai-chinh",
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }), " Mở lô"]
									}), (e.outstanding ?? 0) > 0 && /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => fe(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-emerald-600 text-white text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(ro, { size: 15 }), " Thu tiền"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [de.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Co, { tone: e.statusTone }),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.id
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: e.statusTone,
										size: "sm",
										children: K(e.status)
									}),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
										children: e.currency
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: K(e.customer)
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 mt-2.5 text-center",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-slate-50 border p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-slate-500 font-semibold",
											children: "Phải thu"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px]",
											children: G(e.receivable, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-emerald-50 border border-emerald-200 p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-emerald-700 font-semibold",
											children: "Đã thu"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-emerald-700",
											children: G(e.received, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-red-50 border border-red-200 p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-red-600 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-red-700",
											children: G(e.outstanding, e.currency)
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-2",
								children: [
									"Sale ",
									K(e.sale),
									" · cập nhật bởi ",
									K(e.support)
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/lo-hang/" + e.id + "?tab=tai-chinh",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 17 }), " MỞ LÔ"]
						}), (e.outstanding ?? 0) > 0 ? /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => fe(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-emerald-600 text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ro, { size: 17 }), " THU TIỀN"]
						}) : /* @__PURE__ */ (0, R.jsx)("span", {
							className: "flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]",
							children: "Đã thu đủ"
						})]
					})]
				}, e.id)), de.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy lô nào"
					}), /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Thử từ khóa khác hoặc bỏ bớt bộ lọc."
					})]
				})]
			}),
			A && /* @__PURE__ */ (0, R.jsxs)(ko, {
				id: "receivable-pay-sheet",
				testId: "receivable-pay-sheet",
				labelledBy: "receivable-pay-title",
				pending: !!F,
				width: 480,
				onClose: () => ee(null),
				children: [
					/* @__PURE__ */ (0, R.jsxs)("h3", {
						id: "receivable-pay-title",
						className: "font-extrabold text-[18px] text-[#0f2a4a]",
						children: ["Ghi nhận khoản thu — ", A.id]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1",
						children: [
							"Khách ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: K(A.customer) }),
							" · Còn phải thu: ",
							/* @__PURE__ */ (0, R.jsx)("b", {
								className: "text-red-700",
								children: G(A.outstanding, A.currency)
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Loại khoản",
							children: /* @__PURE__ */ (0, R.jsxs)("select", {
								value: N,
								disabled: !!F,
								onChange: (e) => {
									te(e.target.value), P.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
								},
								className: X(),
								children: [
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu tiền khách" }),
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu tạm ứng" }),
									/* @__PURE__ */ (0, R.jsx)("option", { children: "Thu nốt công nợ" })
								]
							})
						}), /* @__PURE__ */ (0, R.jsx)(Y, {
							label: `Số tiền (${A.currency})`,
							required: !0,
							error: j ? void 0 : "Nhập số tiền — VD: 150000000",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: j,
								disabled: !!F,
								onChange: (e) => {
									M(e.target.value), P.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
								},
								inputMode: "numeric",
								placeholder: "VD: 150000000",
								className: X(j ? "ok" : "missing")
							})
						})]
					}),
					F ? /* @__PURE__ */ (0, R.jsx)("p", {
						role: "status",
						"data-testid": "receivable-pay-pending",
						className: "mt-2.5 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13.5px] font-semibold text-blue-800",
						children: "⏳ ĐANG CHỜ BACKEND XÁC NHẬN… Không gửi lại và không đóng trang."
					}) : /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-2",
						children: [
							"Ghi theo đồng tiền của lô (",
							A.currency,
							") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai."
						]
					}),
					ie && /* @__PURE__ */ (0, R.jsx)("p", {
						role: "alert",
						id: "receivable-pay-error",
						className: "mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700",
						children: ie
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-400 mt-2",
						children: ["Mã yêu cầu: ", /* @__PURE__ */ (0, R.jsx)("b", {
							className: "font-mono",
							children: P.current
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
							onClick: () => ee(null),
							disabled: !!F,
							children: "Hủy"
						}), /* @__PURE__ */ (0, R.jsx)(To, {
							onClick: () => {
								if (re.current || !A) return;
								let e = j.trim(), r = yo(e);
								if (r == null || r <= 0) {
									n("Chưa nhập số tiền", `Nhập số tiền ${A.currency} rồi bấm Lưu — ví dụ 50.000.000.`, "red");
									return;
								}
								if (!t("payment_record", {
									shipmentId: A.id,
									amount: e,
									requestId: P.current,
									date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
									note: N
								})) {
									n("Không gửi được", "Component chưa kết nối backend.", "red");
									return;
								}
								ae(""), re.current = P.current, ne(P.current);
							},
							testId: "receivable-pay-submit",
							disabled: !!F,
							children: F ? "⏳ ĐANG CHỜ BACKEND XÁC NHẬN…" : "💾 LƯU KHOẢN THU"
						})]
					})
				]
			}),
			de.length > 0 && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "md:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: /* @__PURE__ */ (0, R.jsxs)(L, {
					to: "/lo-hang",
					className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px] flex items-center justify-center",
					children: ["XEM LÔ HÀNG ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
				})
			})
		]
	});
}
//#endregion
//#region src/pages/PartnerPayables.tsx
var ys = (e) => e === "CONFIRMED" ? "blue" : e === "REVIEW_REQUIRED" ? "amber" : "gray";
function bs() {
	let { payables: e, dispatch: t, toast: n } = Jn(), [r, i] = (0, _.useState)(""), [a, o] = (0, _.useState)(!1), [s, c] = (0, _.useState)(!1), [l, u] = (0, _.useState)("ALL"), [d, f] = (0, _.useState)("ALL"), [p, m] = (0, _.useState)("ALL"), [h, g] = (0, _.useState)(null), [v, y] = (0, _.useState)(""), b = (0, _.useRef)(""), x = e.rows ?? [], S = e.totals ?? {}, C = ["ALL", ...Array.from(new Set(x.map((e) => e.currency)))], w = ["ALL", ...Array.from(new Set(x.map((e) => e.partnerId)))], T = ["ALL", ...Array.from(new Set(x.map((e) => e.status)))], E = (e) => x.find((t) => t.partnerId === e)?.partnerName ?? e, D = (0, _.useMemo)(() => {
		let e = r.trim().toLowerCase();
		return x.filter((t) => !(s && !(t.remaining != null && t.remaining > 0) || l !== "ALL" && t.currency !== l || d !== "ALL" && t.partnerId !== d || p !== "ALL" && t.status !== p || e && !(t.shipmentId + " " + t.partnerName + " " + t.partnerId).toLowerCase().includes(e))).sort((e, t) => (t.remaining ?? -1) - (e.remaining ?? -1));
	}, [
		x,
		r,
		s,
		l,
		d,
		p
	]), O = (e) => {
		b.current = `PPAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, y(""), g(e);
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(ro, {
							size: 20,
							className: "text-[#1e5aa8]"
						}),
						title: "Thanh toán đối tác · Phải trả",
						sub: "Toàn bộ phải trả đối tác theo lô — đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 mt-3",
						children: [Object.keys(S).length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có khoản phải trả đối tác nào được ghi nhận — phải trả đang ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
								", không phải 0."
							]
						}), Object.entries(S).map(([e, t]) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 mb-2",
								children: [/* @__PURE__ */ (0, R.jsxs)("span", {
									className: "text-[12px] font-extrabold uppercase tracking-wider text-slate-500",
									children: ["Tổng phải trả · ", e]
								}), /* @__PURE__ */ (0, R.jsx)("span", {
									className: "text-[11px] text-slate-400",
									children: "không quy đổi sang đồng tiền khác"
								})]
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 text-center",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-white border p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-slate-500 font-semibold",
											children: "Phải trả"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]",
											children: G(t.payable, e)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-blue-700 font-semibold",
											children: "Đã trả"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-blue-700",
											children: G(t.paid, e)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-amber-50 border border-amber-200 p-3",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-amber-700 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[16px] md:text-[18px] text-amber-800",
											children: G(t.remaining, e)
										})]
									})
								]
							})]
						}, e))]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex gap-2 mt-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: r,
								onChange: (e) => i(e.target.value),
								placeholder: "Tìm mã lô (LO-0308), đối tác (Phú Anh), mã đối tác…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						}), /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => o((e) => !e),
							className: U("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", a ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white"),
							children: [
								/* @__PURE__ */ (0, R.jsx)(Fa, { size: 18 }),
								" ",
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "hidden sm:inline",
									children: "Lọc"
								})
							]
						})]
					}),
					a && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => c((e) => !e),
								className: U("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", s ? "border-amber-400 bg-amber-50 text-amber-800" : "border-slate-200 bg-white text-slate-600"),
								children: [/* @__PURE__ */ (0, R.jsx)(Wr, { size: 16 }), " Chỉ còn phải trả"]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đồng tiền:"
								}), C.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => u(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", l === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Đối tác:"
								}), w.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => f(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", d === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : K(E(e))
								}, e))]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "self-center text-[13px] font-bold text-slate-500",
									children: "Trạng thái:"
								}), T.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
									onClick: () => m(e),
									className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", p === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
									children: e === "ALL" ? "Tất cả" : e
								}, e))]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [D.length, " dòng"]
							}),
							" · Ưu tiên theo còn phải trả thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: /* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[1080px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Lô" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Đối tác" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Phải trả" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Đã trả" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Còn lại" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Đồng tiền" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: D.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(L, {
									to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.shipmentId
								}) }),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "font-semibold max-w-[220px]",
									children: [/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "inline-flex items-center gap-1.5",
										children: [
											/* @__PURE__ */ (0, R.jsx)(Mr, {
												size: 15,
												className: "text-[#1e5aa8] shrink-0"
											}),
											" ",
											K(e.partnerName)
										]
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[12px] text-slate-400 font-normal",
										children: e.partnerId
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold",
									children: G(e.payable, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "text-blue-700 font-semibold",
									children: G(e.paid, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: U("font-extrabold", !mo(e.remaining) && (e.remaining ?? 0) > 0 ? "text-amber-800" : "text-slate-500"),
									children: G(e.remaining, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("span", {
									className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
									children: e.currency
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: ys(e.status),
									size: "sm",
									children: e.status
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, R.jsxs)(L, {
										to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }), " Mở lô"]
									}), (e.remaining ?? 0) > 0 && /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => O(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(ro, { size: 15 }), " Trả đối tác"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [D.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Co, { tone: ys(e.status) }),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "font-extrabold text-[17px] text-[#0f2a4a]",
										children: e.shipmentId
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: ys(e.status),
										size: "sm",
										children: e.status
									}),
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
										children: e.currency
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: [
									K(e.partnerName),
									" ",
									/* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-slate-400 font-normal text-[12.5px]",
										children: e.partnerId
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 mt-2.5 text-center",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-slate-50 border p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-slate-500 font-semibold",
											children: "Phải trả"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px]",
											children: G(e.payable, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-blue-50 border border-blue-200 p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-blue-700 font-semibold",
											children: "Đã trả"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-blue-700",
											children: G(e.paid, e.currency)
										})]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "rounded-xl bg-amber-50 border border-amber-200 p-2.5",
										children: [/* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[11px] text-amber-700 font-semibold",
											children: "Còn lại"
										}), /* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-extrabold text-[14px] text-amber-800",
											children: G(e.remaining, e.currency)
										})]
									})
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/lo-hang/" + e.shipmentId + "?tab=tai-chinh",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 17 }), " MỞ LÔ"]
						}), (e.remaining ?? 0) > 0 ? /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => O(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ro, { size: 17 }), " TRẢ ĐỐI TÁC"]
						}) : /* @__PURE__ */ (0, R.jsx)("span", {
							className: "flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]",
							children: "Đã trả đủ"
						})]
					})]
				}, e.id)), D.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Chưa có khoản phải trả đối tác"
					}), /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Chưa có nghĩa vụ / thanh toán canonical nào cho các lô hiện tại — phải trả là “chưa xác định”, không phải 0."
					})]
				})]
			}),
			h && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => g(null)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Ghi nhận thanh toán đối tác — ", h.shipmentId]
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[13.5px] text-slate-500 mt-1",
							children: [
								"Đối tác ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: K(h.partnerName) }),
								" (",
								h.partnerId,
								") · Còn phải trả: ",
								/* @__PURE__ */ (0, R.jsx)("b", {
									className: "text-amber-800",
									children: G(h.remaining, h.currency)
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-3 mt-3",
							children: /* @__PURE__ */ (0, R.jsx)(Y, {
								label: `Số tiền (${h.currency})`,
								required: !0,
								error: v ? void 0 : "Nhập số tiền — VD: 20000000",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: v,
									onChange: (e) => y(e.target.value),
									inputMode: "numeric",
									placeholder: "VD: 20000000",
									className: X(v ? "ok" : "missing")
								})
							})
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: [
								"Ghi theo đồng tiền của lô (",
								h.currency,
								") — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản trả thứ hai."
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => g(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsx)(To, {
								onClick: () => {
									if (!h) return;
									let e = v.trim(), r = yo(e);
									if (r == null || r <= 0) {
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
									n("Đã gửi thanh toán " + G(r, h.currency), "Ghi qua canonical ledger (transaction + allocation) — backend sẽ đọc lại còn phải trả.", "green"), g(null), y("");
								},
								children: "💸 LƯU THANH TOÁN"
							})]
						})
					]
				})]
			}),
			D.length > 0 && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "md:hidden sticky-action -mx-3 px-3 py-3 flex gap-2",
				children: /* @__PURE__ */ (0, R.jsxs)(L, {
					to: "/lo-hang",
					className: "btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px] flex items-center justify-center",
					children: ["XEM LÔ HÀNG ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
				})
			})
		]
	});
}
//#endregion
//#region src/pages/Customers.tsx
var xs = {
	id: "",
	name: "",
	phone: "",
	email: "",
	contactPerson: "",
	taxCode: "",
	address: "",
	note: ""
};
function Ss() {
	let { customers: e, dispatch: t, toast: n, role: r } = Jn(), i = (0, _.useSyncExternalStore)(C, S, S), [a, o] = Ro("q"), [s, c] = (0, _.useState)(!1), [l, u] = (0, _.useState)(null), [d, f] = (0, _.useState)(null), [p, m] = (0, _.useState)(!1), [h, g] = (0, _.useState)(xs), [v, y] = (0, _.useState)(""), [b, x] = (0, _.useState)(""), [w, T] = (0, _.useState)(null), [E, D] = (0, _.useState)(""), O = (0, _.useMemo)(() => e.filter((e) => !a || (e.id + e.name + e.short + e.mst + e.taxCode + e.phone + e.email).toLowerCase().includes(a.toLowerCase())), [e, a]), k = (e, t) => g((n) => ({
		...n,
		[e]: t
	})), A = () => {
		g(xs), D(""), c(!0);
	}, ee = (e) => {
		D(""), g({
			id: e.id,
			name: e.name,
			phone: e.phone,
			email: e.email,
			contactPerson: e.contactPerson,
			taxCode: e.taxCode,
			address: e.address,
			note: e.note
		}), u(e);
	};
	return (0, _.useEffect)(() => {
		if (!w || !i) return;
		let e = (i.lastWrites ?? []).find((e) => e.event === w.event && e.requestId === w.requestId);
		e && (e.ok ? (i.customers ?? []).some((e) => e.id === w.id) ? (T(null), c(!1), u(null), g(xs), D(""), n(w.event === "customer_create" ? "Đã tạo khách hàng " + w.id : "Đã lưu khách hàng " + w.id, "Backend ghi + audit thành công; khách hàng đã có trong dữ liệu mới.", "green")) : (T(null), D("Backend báo thành công nhưng khách hàng chưa xuất hiện trong dữ liệu mới — biểu mẫu được giữ nguyên.")) : (T(null), D(e.error || "Backend từ chối yêu cầu."), n("Không lưu được khách hàng", e.error || "Backend từ chối.", "red")));
	}, [
		i,
		w,
		n
	]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(to, { size: 18 }),
						title: "Khách Hàng",
						sub: "Tìm theo mã · tên · MST · SĐT · email — tạo, sửa, lưu trữ và import qua backend Logistics thật",
						right: /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex gap-2",
							children: [/* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: () => m(!0),
								className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, R.jsx)(Ya, { size: 17 }), " Import"]
							}), /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: A,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }), " Khách mới"]
							})]
						})
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
							size: 19,
							className: "ml-3.5 text-slate-400 shrink-0"
						}), /* @__PURE__ */ (0, R.jsx)("input", {
							value: a,
							onChange: (e) => o(e.target.value),
							placeholder: "Nhập mã (CUST-ANPHAT), tên (An Phát), MST…",
							className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-2.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [O.length, " khách hàng"]
							}),
							a ? /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
								" cho “",
								a,
								"”"
							] }) : null,
							" · Mỗi khách hiển thị: mã · MST · liên hệ · địa chỉ."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[880px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã KH" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Tên khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "MST" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Liên hệ" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Địa chỉ" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: O.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[220px]",
									children: e.name
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: K(e.taxCode) }),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "text-[13px]",
									children: [/* @__PURE__ */ (0, R.jsx)("span", {
										className: "block",
										children: K(e.contactPerson)
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-slate-500",
										children: K(e.phone)
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "max-w-[240px] text-[13px] text-slate-600",
									children: K(e.address)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex gap-1.5",
									children: [/* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => ee(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 15 }), " Sửa"]
									}), r === "ADMIN" && /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => f(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-red-200 text-red-700 text-[13px] font-bold px-3 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(ur, { size: 15 }), " Lưu trữ"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), O.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy khách hàng nào"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo khách mới."
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: A,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Khách mới"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [O.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[17px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsxs)(q, {
									tone: "blue",
									size: "sm",
									children: ["MST ", K(e.taxCode)]
								})]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.name
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13px] text-slate-500",
								children: K(e.address)
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] text-slate-400 mt-1",
								children: [
									K(e.contactPerson),
									" · ",
									K(e.phone)
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid grid-cols-2 border-t",
						children: [/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => ee(e),
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 17 }), " SỬA"]
						}), r === "ADMIN" ? /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => f(e),
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-red-700 min-h-[52px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ur, { size: 17 }), " LƯU TRỮ"]
						}) : /* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/kinh-doanh-bao-gia",
							className: "touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]",
							children: ["BÁO GIÁ ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
						})]
					})]
				}, e.id)), O.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy khách hàng nào"
					}), /* @__PURE__ */ (0, R.jsxs)("button", {
						onClick: A,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Khách mới"]
					})]
				})]
			}),
			(s || l) && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => {
						w || (c(!1), u(null), D(""));
					}
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: l ? "Sửa khách hàng " + l.id : "Tạo khách hàng mới"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Mọi thay đổi đi qua backend Logistics (RBAC + audit)."
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Mã khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.id,
										disabled: !!l,
										onChange: (e) => k("id", e.target.value),
										placeholder: "VD: CUST-ABC",
										className: X(h.id ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Tên khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.name,
										onChange: (e) => k("name", e.target.value),
										placeholder: "Công ty / cá nhân",
										className: X(h.name ? "ok" : "missing")
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Mã số thuế",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.taxCode,
										onChange: (e) => k("taxCode", e.target.value),
										placeholder: "MST",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Người liên hệ",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.contactPerson,
										onChange: (e) => k("contactPerson", e.target.value),
										placeholder: "Tên người liên hệ",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Số điện thoại",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.phone,
										onChange: (e) => k("phone", e.target.value),
										placeholder: "SĐT",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Email",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: h.email,
										onChange: (e) => k("email", e.target.value),
										placeholder: "email",
										className: X()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid gap-3 mt-3",
							children: [/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Địa chỉ",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: h.address,
									onChange: (e) => k("address", e.target.value),
									placeholder: "Địa chỉ kho / văn phòng",
									className: X()
								})
							}), /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ghi chú",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: h.note,
									onChange: (e) => k("note", e.target.value),
									placeholder: "Ghi chú nội bộ",
									className: X()
								})
							})]
						}),
						E && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5",
							role: "alert",
							children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
								size: 18,
								className: "text-red-600 shrink-0 mt-0.5"
							}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-extrabold text-[14.5px] text-red-800",
								children: "Chưa lưu được — dữ liệu vẫn được giữ"
							}), /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[13.5px] text-red-700 mt-0.5 break-words",
								children: E
							})] })]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => {
									w || (c(!1), u(null), D(""));
								},
								disabled: !!w,
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsx)(To, {
								onClick: () => {
									if (w) return;
									let e = h.id.trim().toUpperCase();
									if (!e || !h.name.trim()) {
										n("Thiếu thông tin", "Mã và tên khách hàng là bắt buộc.", "red");
										return;
									}
									let r = l ? "customer_edit" : "customer_create", i = `cust-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
									if (!(l ? t("customer_edit", {
										id: e,
										name: h.name.trim(),
										phone: h.phone.trim(),
										email: h.email.trim(),
										contact_person: h.contactPerson.trim(),
										tax_code: h.taxCode.trim(),
										address: h.address.trim(),
										note: h.note.trim(),
										requestId: i
									}) : t("customer_create", {
										id: e,
										name: h.name.trim(),
										phone: h.phone.trim(),
										email: h.email.trim(),
										contactPerson: h.contactPerson.trim(),
										taxCode: h.taxCode.trim(),
										address: h.address.trim(),
										note: h.note.trim(),
										requestId: i
									}))) {
										D("Không gửi được yêu cầu — component chưa kết nối backend. Dữ liệu bạn nhập vẫn được giữ nguyên."), n("Không gửi được", "Component chưa kết nối backend; chưa có gì được lưu.", "red");
										return;
									}
									D(""), T({
										event: r,
										id: e,
										requestId: i
									}), n(l ? "Đã gửi cập nhật " + e : "Đã gửi yêu cầu tạo " + e, "Đang chờ backend xác nhận…", "blue");
								},
								disabled: !!w,
								children: w ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: ["💾 ", l ? "LƯU THAY ĐỔI" : "TẠO KHÁCH HÀNG"] })
							})]
						})
					]
				})]
			}),
			d && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => f(null)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[460px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: [
								"Lưu trữ ",
								d.id,
								"?"
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[14.5px] text-slate-600 mt-1.5",
							children: [
								"Khách ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: d.name }),
								" sẽ bị soft-delete (không xóa vật lý). Chỉ Admin có quyền."
							]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Lý do lưu trữ",
								required: !0,
								error: v ? void 0 : "Nhập lý do trước khi lưu trữ",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: v,
									onChange: (e) => y(e.target.value),
									placeholder: "VD: ngừng hợp tác",
									className: X(v ? "ok" : "missing")
								})
							})
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => f(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsx)("button", {
								onClick: () => {
									if (d) {
										if (!v.trim()) {
											n("Cần lý do lưu trữ", "Nhập lý do trước khi lưu trữ khách hàng.", "red");
											return;
										}
										t("customer_archive", {
											id: d.id,
											reason: v.trim()
										}), n("Đã gửi lưu trữ " + d.id, "Chỉ Admin có quyền; backend kiểm tra RBAC.", "blue"), f(null), y("");
									}
								},
								className: "btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-[15.5px] px-5 min-h-[48px]",
								children: "LƯU TRỮ"
							})]
						})
					]
				})]
			}),
			p && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => m(!1)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: "Import khách hàng"
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[13.5px] text-slate-500",
							children: ["Mỗi dòng một khách: ", /* @__PURE__ */ (0, R.jsx)("b", { children: "Mã;Tên;MST;SĐT;Email;Địa chỉ" })]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Dữ liệu (mỗi dòng 1 khách)",
								children: /* @__PURE__ */ (0, R.jsx)("textarea", {
									value: b,
									onChange: (e) => x(e.target.value),
									rows: 6,
									placeholder: "CUST-XYZ;Khách XYZ;0109999000;0988111222;xyz@example.com;KCN Test",
									className: U(X(), "font-mono text-[13.5px]")
								})
							})
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-4",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => m(!1),
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: () => {
									let e = b.split(/\r?\n/).map((e) => e.trim()).filter(Boolean).map((e) => {
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
									t("customer_import", { rows: e }), n("Đã gửi import " + e.length + " khách hàng", "Backend bỏ qua mã đã tồn tại.", "blue"), m(!1), x("");
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
var Cs = {
	DRAFT: "Nháp",
	READY_FOR_REVIEW: "Chờ review",
	SENT: "Đã gửi khách",
	ACCEPTED: "Khách chốt",
	REJECTED: "Từ chối",
	EXPIRED: "Hết hạn",
	READY_TO_CREATE_SHIPMENT: "Sẵn sàng tạo lô"
}, ws = {
	DRAFT: "gray",
	READY_FOR_REVIEW: "blue",
	SENT: "amber",
	ACCEPTED: "green",
	REJECTED: "red",
	EXPIRED: "gray",
	READY_TO_CREATE_SHIPMENT: "green"
}, Ts = ["USD", "CNY"], Es = {
	code: "",
	serviceName: "",
	unit: "Lần",
	qty: "1",
	currency: "VND",
	costUnit: "",
	sellUnit: "",
	taxPct: "8"
}, Ds = {
	customerId: "",
	salesOwner: "",
	origin: "",
	destination: "",
	route: "",
	incoterm: "EXW",
	transportMode: "Road",
	goodsDescription: "",
	expectedDeliveryDate: "",
	lines: [{ ...Es }],
	fx: {
		USD: "",
		CNY: ""
	}
}, Os = (e) => e == null ? "" : Number(e).toLocaleString("vi-VN"), ks = (e) => {
	let t = e.fxRatesToVnd ?? {}, n = (e.fxNeededFor ?? []).filter((e) => t[e] != null).map((e) => `${e} ${Os(t[e])}`);
	return n.length ? "Tỷ giá báo giá: " + n.join(" · ") : "";
};
function As(e) {
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
function js() {
	let [e] = Rn(), { quotes: t, customers: n, dispatch: r, toast: i } = Jn(), [a, o] = (0, _.useState)(e.get("q") ?? ""), s = (t) => {
		o(t);
		let n = new URLSearchParams(e);
		t ? n.set("q", t) : n.delete("q"), window.history.replaceState(null, "", `?${n.toString()}`);
	}, [c, l] = (0, _.useState)("ALL"), [u, d] = (0, _.useState)(!1), [f, p] = (0, _.useState)(null), [m, h] = (0, _.useState)(Ds), g = (0, _.useMemo)(() => t.filter((e) => (c === "ALL" || e.status === c) && (!a || (e.id + e.quoteNo + e.customer + e.salesOwner + e.origin + e.destination).toLowerCase().includes(a.toLowerCase()))), [
		t,
		a,
		c
	]), v = ["ALL", ...Array.from(new Set(t.map((e) => e.status)))], y = Ts.filter((e) => m.lines.some((t) => (t.currency || "VND").trim().toUpperCase() === e)), b = (e, t) => h((n) => ({
		...n,
		[e]: t
	})), x = (e, t) => h((n) => ({
		...n,
		fx: {
			...n.fx,
			[e]: t
		}
	})), S = (e, t, n) => h((r) => ({
		...r,
		lines: r.lines.map((r, i) => i === e ? {
			...r,
			[t]: n
		} : r)
	})), C = () => h((e) => ({
		...e,
		lines: [...e.lines, { ...Es }]
	})), w = (e) => h((t) => ({
		...t,
		lines: t.lines.length > 1 ? t.lines.filter((t, n) => n !== e) : t.lines
	})), T = () => {
		h({
			...Ds,
			lines: [{ ...Es }],
			fx: {
				USD: "",
				CNY: ""
			},
			salesOwner: "Minh Tú"
		}), d(!0);
	}, E = (e) => {
		h({
			customerId: e.customerId,
			salesOwner: e.salesOwner,
			origin: e.origin,
			destination: e.destination,
			route: e.route,
			incoterm: e.incoterm,
			transportMode: e.transportMode,
			goodsDescription: e.goodsDescription,
			expectedDeliveryDate: e.expectedDeliveryDate,
			lines: e.serviceLines.length ? e.serviceLines.map(As) : [{ ...Es }],
			fx: {
				USD: Os(e.fxRatesToVnd?.USD),
				CNY: Os(e.fxRatesToVnd?.CNY)
			}
		}), p(e);
	}, D = () => m.lines.filter((e) => e.code.trim() || e.serviceName.trim()).map((e) => ({
		code: e.code.trim(),
		serviceName: e.serviceName.trim(),
		unit: e.unit.trim() || "Lần",
		qty: e.qty.trim() === "" ? "" : Number(e.qty),
		currency: e.currency.trim() || "VND",
		costUnit: e.costUnit.trim() === "" ? "" : Number(e.costUnit),
		sellUnit: e.sellUnit.trim() === "" ? "" : Number(e.sellUnit),
		taxPct: e.taxPct.trim() === "" ? "" : Number(e.taxPct)
	})), O = () => {
		if (!m.customerId) {
			i("Chưa chọn khách hàng", "Chọn khách hàng trước khi tạo báo giá.", "red");
			return;
		}
		let e = D();
		if (e.length === 0) {
			i("Thiếu dòng dịch vụ", "Cần ít nhất một dòng dịch vụ báo giá.", "red");
			return;
		}
		let t = Ts.filter((t) => e.some((e) => e.currency === t)), n = t.filter((e) => {
			let t = String(m.fx[e] ?? "").replace(/\s|\./g, "").replace(",", "."), n = Number(t);
			return !(t.trim() !== "" && Number.isFinite(n) && n > 0);
		});
		if (n.length > 0) {
			i("Thiếu tỷ giá báo giá", "Cần tỷ giá " + n.map((e) => e + " → VND").join(", ") + " cho các dòng ngoại tệ. Hệ thống không tự đặt tỷ giá.", "red");
			return;
		}
		let a = {};
		for (let e of t) {
			let t = String(m.fx[e]).replace(/\s|\./g, "").replace(",", ".");
			a[e] = Number(t);
		}
		f ? (r("quote_edit", {
			id: f.id,
			sales_owner: m.salesOwner.trim(),
			origin: m.origin.trim(),
			destination: m.destination.trim(),
			route: m.route.trim(),
			incoterm: m.incoterm.trim(),
			goods_description: m.goodsDescription.trim(),
			expected_delivery_date: m.expectedDeliveryDate.trim(),
			serviceLines: e,
			fx: a
		}), i("Đã gửi cập nhật " + f.id, "Backend tính lại giá bán + audit.", "green")) : (r("quote_create", {
			customerId: m.customerId,
			salesOwner: m.salesOwner.trim(),
			origin: m.origin.trim(),
			destination: m.destination.trim(),
			route: m.route.trim(),
			incoterm: m.incoterm.trim(),
			transportMode: m.transportMode.trim(),
			goodsDescription: m.goodsDescription.trim(),
			expectedDeliveryDate: m.expectedDeliveryDate.trim(),
			serviceLines: e,
			fx: a
		}), i("Đã gửi tạo báo giá", "Backend tạo mã Q-… tự động, tính dự toán và audit.", "green")), d(!1), p(null);
	}, k = (e, t) => {
		r("quote_transition", {
			id: e.id,
			nextStatus: t
		}), i("Đã gửi chuyển trạng thái " + e.id, `→ ${Cs[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Pr, { size: 18 }),
						title: "Kinh doanh · Báo giá",
						sub: "Báo giá (estimate) là dự toán LOG-C12 — tách bạch với tài chính thực thu/chi. Tìm theo mã · khách · tuyến.",
						right: /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: T,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }), " Tạo báo giá"]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: a,
								onChange: (e) => s(e.target.value),
								placeholder: "Nhập mã (Q-…), khách (An Phát), tuyến…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: v.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => l(e),
							className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", c === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : Cs[e] ?? e
						}, e))
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [g.length, " báo giá"]
							}),
							" · Trạng thái do backend quyết định theo luồng chốt khách."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[960px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã báo giá" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Tuyến" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Sale" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Tổng (VND)" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: g.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("td", { children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsx)("span", {
									className: "block text-[12px] text-slate-400",
									children: e.quoteNo
								})] }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "max-w-[220px] text-[13px] text-slate-600",
									children: [
										K(e.origin),
										" → ",
										K(e.destination)
									]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: K(e.salesOwner) }),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "font-bold",
									children: [W(e.sellingPriceTotalVnd ?? e.total, "VND"), ks(e) && /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-[11.5px] font-semibold text-slate-400",
										children: ks(e)
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: ws[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex flex-wrap gap-1.5",
									children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, R.jsx)("button", {
										onClick: () => k(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: Cs[t] ?? t
									}, t)), /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => E(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Sửa"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), g.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy báo giá nào"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Tạo báo giá từ khách hàng đã có."
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: T,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo báo giá"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [g.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[16px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsx)(q, {
									tone: ws[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								})]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									K(e.origin),
									" → ",
									K(e.destination)
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "font-extrabold text-[16px] mt-1.5",
								children: [W(e.sellingPriceTotalVnd ?? e.total, "VND"), " ₫"]
							}),
							ks(e) && /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12px] font-semibold text-slate-400 mt-0.5",
								children: ks(e)
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "border-t p-3 flex flex-wrap gap-2",
						children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => k(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: Cs[t] ?? t
						}, t)), /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => E(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Sửa"]
						})]
					})]
				}, e.id)), g.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy báo giá nào"
					}), /* @__PURE__ */ (0, R.jsxs)("button", {
						onClick: T,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo báo giá"]
					})]
				})]
			}),
			(u || f) && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => {
						d(!1), p(null);
					}
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[760px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[92vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: f ? "Sửa báo giá " + f.id : "Tạo báo giá mới"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Dự toán chi phí & giá bán — đi qua backend LOG-C12 (tính toán + audit), không ghi sổ tài chính."
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 mt-4",
							children: [
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Khách hàng",
									required: !0,
									children: /* @__PURE__ */ (0, R.jsxs)("select", {
										value: m.customerId,
										disabled: !!f,
										onChange: (e) => b("customerId", e.target.value),
										className: X(m.customerId ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, R.jsx)("option", {
											value: "",
											children: "-- Chọn khách --"
										}), n.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
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
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Sale phụ trách",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.salesOwner,
										onChange: (e) => b("salesOwner", e.target.value),
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Nơi lấy (origin)",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.origin,
										onChange: (e) => b("origin", e.target.value),
										placeholder: "VD: Bằng Tường (Quảng Tây)",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Nơi giao (destination)",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.destination,
										onChange: (e) => b("destination", e.target.value),
										placeholder: "VD: KCN Quế Võ, Bắc Ninh",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Tuyến / cửa khẩu",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.route,
										onChange: (e) => b("route", e.target.value),
										placeholder: "VD: Hữu Nghị (Lạng Sơn)",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Incoterm",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.incoterm,
										onChange: (e) => b("incoterm", e.target.value),
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Phương thức",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.transportMode,
										onChange: (e) => b("transportMode", e.target.value),
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Ngày giao dự kiến",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: m.expectedDeliveryDate,
										onChange: (e) => b("expectedDeliveryDate", e.target.value),
										placeholder: "VD: 2026-09-20",
										className: X()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Mô tả hàng hóa",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: m.goodsDescription,
								onChange: (e) => b("goodsDescription", e.target.value),
								placeholder: "VD: Linh kiện điện tử",
								className: U(X(), "mt-3")
							})
						}),
						y.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-4 rounded-xl border-2 border-amber-300 bg-amber-50/70 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[15px] text-amber-900",
									children: "Tỷ giá báo giá — bắt buộc cho dòng ngoại tệ"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13px] text-amber-800 mt-0.5",
									children: "Tổng VND của báo giá được quy đổi theo tỷ giá bạn nhập ở đây. Hệ thống không tự đặt tỷ giá và đây không phải tỷ giá giao dịch thực tế."
								}),
								/* @__PURE__ */ (0, R.jsx)("div", {
									className: "grid grid-cols-2 gap-2.5 mt-2.5",
									children: y.map((e) => /* @__PURE__ */ (0, R.jsx)(Y, {
										label: `Tỷ giá ${e} → VND`,
										required: !0,
										hint: "Số có dấu chấm phân cách hàng nghìn.",
										children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: m.fx[e],
											onChange: (t) => x(e, t.target.value),
											inputMode: "decimal",
											placeholder: e === "USD" ? "VD: 25.500" : "VD: 3.650",
											className: X(m.fx[e].trim() ? "ok" : "missing")
										})
									}, e))
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center justify-between mb-2",
								children: [/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-extrabold text-[15px] text-[#0f2a4a]",
									children: "Dòng dịch vụ"
								}), /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: C,
									className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
									children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 15 }), " Thêm dòng"]
								})]
							}), /* @__PURE__ */ (0, R.jsx)("div", {
								className: "space-y-2",
								children: m.lines.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl border border-slate-200 p-3 bg-slate-50/60",
									children: [/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid grid-cols-2 md:grid-cols-4 gap-2",
										children: [
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Mã dịch vụ",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.code,
													onChange: (e) => S(t, "code", e.target.value),
													placeholder: "DV-VC-TQ",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Tên dịch vụ",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.serviceName,
													onChange: (e) => S(t, "serviceName", e.target.value),
													placeholder: "Cước xe TQ",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "ĐVT",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.unit,
													onChange: (e) => S(t, "unit", e.target.value),
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Số lượng",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.qty,
													onChange: (e) => S(t, "qty", e.target.value),
													inputMode: "numeric",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Giá vốn (unit)",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.costUnit,
													onChange: (e) => S(t, "costUnit", e.target.value),
													inputMode: "numeric",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Giá bán (unit)",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.sellUnit,
													onChange: (e) => S(t, "sellUnit", e.target.value),
													inputMode: "numeric",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Thuế %",
												children: /* @__PURE__ */ (0, R.jsx)("input", {
													value: e.taxPct,
													onChange: (e) => S(t, "taxPct", e.target.value),
													inputMode: "numeric",
													className: X()
												})
											}),
											/* @__PURE__ */ (0, R.jsx)(Y, {
												label: "Tiền tệ",
												children: /* @__PURE__ */ (0, R.jsxs)("select", {
													value: e.currency,
													onChange: (e) => S(t, "currency", e.target.value),
													className: X(),
													children: [
														/* @__PURE__ */ (0, R.jsx)("option", { children: "VND" }),
														/* @__PURE__ */ (0, R.jsx)("option", { children: "USD" }),
														/* @__PURE__ */ (0, R.jsx)("option", { children: "CNY" })
													]
												})
											})
										]
									}), m.lines.length > 1 && /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => w(t),
										className: "mt-2 inline-flex items-center gap-1 text-[13px] font-bold text-red-600",
										children: [/* @__PURE__ */ (0, R.jsx)(Ua, { size: 14 }), " Xóa dòng"]
									})]
								}, t))
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => {
									d(!1), p(null);
								},
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsxs)(To, {
								onClick: O,
								children: ["💾 ", f ? "LƯU BÁO GIÁ" : "TẠO BÁO GIÁ"]
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
var Ms = {
	DRAFT: "Nháp",
	REVIEWING: "Đang review",
	AGREED: "Đã đồng ý",
	REVISED: "Đã sửa đổi",
	VOID: "Vô hiệu"
}, Ns = {
	DRAFT: "gray",
	REVIEWING: "blue",
	AGREED: "green",
	REVISED: "amber",
	VOID: "red"
}, Ps = [
	"accepted_quotation",
	"signed_contract",
	"customer_confirmation",
	"entrusted_documentation"
], Fs = {
	accepted_quotation: "Báo giá được khách chốt",
	signed_contract: "Hợp đồng đã ký",
	customer_confirmation: "Khách xác nhận (email/tin nhắn)",
	entrusted_documentation: "Chứng từ ủy thác nhập khẩu"
};
function Is() {
	let { agreements: e, quotes: t, dispatch: n, toast: r } = Jn(), [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("ALL"), [c, l] = (0, _.useState)(!1), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)({}), x = (0, _.useMemo)(() => e.filter((e) => (o === "ALL" || e.status === o) && (!i || (e.id + e.agreementNo + e.customer + e.quoteReference).toLowerCase().includes(i.toLowerCase()))), [
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
		for (let n of Ps) t[n] = !!e.evidence?.[n];
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
				...Ps.reduce((e, t) => ({
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
		}), r("Đã gửi chuyển trạng thái " + e.id, `→ ${Ms[t] ?? t}. Backend kiểm tra đúng luồng.`, "blue");
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(gi, { size: 18 }),
						title: "Thỏa thuận mua bán · Bàn giao",
						sub: "Đóng băng điều khoản thương mại từ báo giá đã chốt — KHÔNG phải tài chính thực thu/chi",
						right: /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: w,
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }), " Tạo thỏa thuận"]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: i,
								onChange: (e) => a(e.target.value),
								placeholder: "Nhập mã thỏa thuận, khách, báo giá nguồn…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: S.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => s(e),
							className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", o === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : Ms[e] ?? e
						}, e))
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [x.length, " thỏa thuận"]
							}),
							" · Trạng thái & bàn giao do backend quyết định."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[960px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Mã thỏa thuận" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Báo giá nguồn" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Bàn giao" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: x.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("td", { children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[#1e5aa8] text-[15px]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsx)("span", {
									className: "block text-[12px] text-slate-400",
									children: e.agreementNo
								})] }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.customer
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "text-[13px] text-slate-600",
									children: K(e.quoteReference)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: Ns[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "max-w-[220px]",
									children: /* @__PURE__ */ (0, R.jsx)(q, {
										tone: e.handoff.state === "READY_FOR_OPERATIONS" ? "green" : e.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber",
										size: "sm",
										children: e.handoff.label
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex flex-wrap gap-1.5",
									children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, R.jsx)("button", {
										onClick: () => O(e, t),
										className: "btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: Ms[t] ?? t
									}, t)), /* @__PURE__ */ (0, R.jsxs)("button", {
										onClick: () => T(e),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]",
										children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Sửa"]
									})]
								}) })
							]
						}, e.id)) })]
					})
				}), x.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Chưa có thỏa thuận nào"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Tạo từ báo giá đã được khách chốt (ACCEPTED)."
						}),
						/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: w,
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo thỏa thuận"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [x.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[16px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsx)(q, {
									tone: Ns[e.status] ?? "gray",
									size: "sm",
									children: e.statusLabel || e.status
								})]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.customer
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: ["Nguồn: ", K(e.quoteReference)]
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "mt-2",
								children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: e.handoff.state === "READY_FOR_OPERATIONS" ? "green" : e.handoff.state === "MISSING_REQUIRED_DATA" ? "red" : "amber",
									size: "sm",
									children: e.handoff.label
								})
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "border-t p-3 flex flex-wrap gap-2",
						children: [e.allowedTransitions.map((t) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => O(e, t),
							className: "btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
							children: Ms[t] ?? t
						}, t)), /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => T(e),
							className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
							children: [/* @__PURE__ */ (0, R.jsx)(sa, { size: 14 }), " Sửa"]
						})]
					})]
				}, e.id)), x.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Chưa có thỏa thuận nào"
					}), /* @__PURE__ */ (0, R.jsxs)("button", {
						onClick: w,
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo thỏa thuận"]
					})]
				})]
			}),
			c && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => l(!1)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[520px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up",
					children: [
						/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: "Tạo thỏa thuận từ báo giá chốt"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Chỉ báo giá ACCEPTED / sẵn sàng tạo lô mới dùng được."
						}),
						C.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4 text-[14px] text-amber-900",
							children: [
								"Chưa có báo giá ACCEPTED. Vào ",
								/* @__PURE__ */ (0, R.jsx)(L, {
									to: "/kinh-doanh-bao-gia",
									className: "font-bold underline",
									children: "Kinh doanh · Báo giá"
								}),
								" để chốt khách trước."
							]
						}) : /* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-3 mt-4",
							children: /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Báo giá nguồn",
								required: !0,
								children: /* @__PURE__ */ (0, R.jsxs)("select", {
									value: f,
									onChange: (e) => p(e.target.value),
									className: X(f ? "ok" : "missing"),
									children: [/* @__PURE__ */ (0, R.jsx)("option", {
										value: "",
										children: "-- Chọn báo giá đã chốt --"
									}), C.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
										value: e.id,
										children: [
											e.id,
											" · ",
											e.customer,
											" · ",
											W(e.sellingPriceTotalVnd ?? e.total),
											" ₫"
										]
									}, e.id))]
								})
							})
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => l(!1),
								children: "Hủy"
							}), C.length > 0 ? /* @__PURE__ */ (0, R.jsx)(To, {
								onClick: E,
								children: "TẠO"
							}) : /* @__PURE__ */ (0, R.jsx)(wo, {
								onClick: () => {
									l(!1);
								},
								children: "ĐÓNG"
							})]
						})
					]
				})]
			}),
			u && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "fixed inset-0 z-50 flex items-end sm:items-center justify-center",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "absolute inset-0 bg-slate-900/55 anim-fade",
					onClick: () => d(null)
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative bg-white w-full sm:max-w-[560px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[90vh] overflow-auto",
					style: { paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" },
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[18px] text-[#0f2a4a]",
							children: ["Sửa thỏa thuận ", u.id]
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500",
							children: "Điều khoản thương mại & bằng chứng bàn giao — ghi qua backend, không phải tài chính."
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-4",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-extrabold text-[14.5px] text-[#0f2a4a] mb-2",
								children: "Bằng chứng chấp nhận"
							}), /* @__PURE__ */ (0, R.jsx)("div", {
								className: "grid sm:grid-cols-2 gap-2",
								children: Ps.map((e) => /* @__PURE__ */ (0, R.jsxs)("label", {
									className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-3 cursor-pointer",
									children: [/* @__PURE__ */ (0, R.jsx)("input", {
										type: "checkbox",
										checked: !!y[e],
										onChange: (t) => b((n) => ({
											...n,
											[e]: t.target.checked
										})),
										className: "w-5 h-5 accent-[#0f2a4a]"
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "text-[14px] font-semibold text-slate-700",
										children: Fs[e]
									})]
								}, e))
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid gap-3 mt-4",
							children: [/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Giả định thương mại (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, R.jsx)("textarea", {
									value: m,
									onChange: (e) => h(e.target.value),
									rows: 4,
									className: X()
								})
							}), /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Vấn đề chưa giải quyết (mỗi dòng một mục)",
								children: /* @__PURE__ */ (0, R.jsx)("textarea", {
									value: g,
									onChange: (e) => v(e.target.value),
									rows: 3,
									placeholder: "Các vấn đề chặn bàn giao vận hành",
									className: X()
								})
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 gap-2.5 mt-5",
							children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
								onClick: () => d(null),
								children: "Hủy"
							}), /* @__PURE__ */ (0, R.jsx)(wo, {
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
function Ls() {
	let { contracts: e } = Jn(), [t, n] = Ro("q"), [r, i] = Ro("kind"), a = r || "ALL", o = (e) => i(e === "ALL" ? "" : e), s = (0, _.useMemo)(() => e.filter((e) => (a === "ALL" || e.kind === a) && (!t || (e.id + e.contractNo + e.client + e.company + e.agent).toLowerCase().includes(t.toLowerCase()))), [
		e,
		t,
		a
	]), c = ["ALL", ...Array.from(new Set(e.map((e) => e.kind).filter(Boolean)))];
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(wi, { size: 18 }),
						title: "Hợp đồng",
						sub: "HDMB · HDNT · PL — tìm theo số hợp đồng, khách, công ty, đại lý",
						right: /* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/hop-dong/moi",
							className: "btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }), " Tạo hợp đồng"]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2",
						children: /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}), /* @__PURE__ */ (0, R.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								placeholder: "Nhập số hợp đồng (HDMB-0306), khách (An Phát)…",
								className: "w-full bg-transparent px-3 py-3 text-[15px] outline-none"
							})]
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1",
						children: c.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => o(e),
							className: U("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", a === e ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"),
							children: e === "ALL" ? "Tất cả" : e
						}, e))
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] text-slate-500 mt-1.5",
						children: [
							"Tìm thấy ",
							/* @__PURE__ */ (0, R.jsxs)("b", {
								className: "text-[#0f2a4a]",
								children: [s.length, " hợp đồng"]
							}),
							" · Mở để xem hàng hóa, sinh chứng từ và liên kết lô."
						]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "tbl w-full text-[14px] min-w-[880px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Số hợp đồng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Loại" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách hàng" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Công ty · Đại lý" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Giá trị" }),
							/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
						] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: s.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "hover:bg-slate-50",
							children: [
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(L, {
									to: Yn(e.id),
									className: "font-extrabold text-[#1e5aa8] hover:underline text-[15px]",
									children: e.id
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(q, {
									tone: "blue",
									size: "sm",
									children: e.kind || "—"
								}) }),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-semibold max-w-[180px]",
									children: e.client || "—"
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "text-[13px] text-slate-600",
									children: [/* @__PURE__ */ (0, R.jsx)("span", {
										className: "block",
										children: e.company || "—"
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "block text-slate-400",
										children: e.agent || "—"
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "font-bold",
									children: W(e.value, e.currency)
								}),
								/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("div", {
									className: "flex gap-1.5",
									children: /* @__PURE__ */ (0, R.jsxs)(L, {
										to: Yn(e.id),
										className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]",
										children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }), " MỞ"]
									})
								}) })
							]
						}, e.id)) })]
					})
				}), s.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "p-8 text-center",
					children: [
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-bold text-[16px]",
							children: "Không tìm thấy hợp đồng nào"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[14px] text-slate-500 mt-1",
							children: "Thử từ khóa khác hoặc tạo hợp đồng mới."
						}),
						/* @__PURE__ */ (0, R.jsxs)(L, {
							to: "/hop-dong/moi",
							className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo hợp đồng"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "md:hidden space-y-3",
				children: [s.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex items-center gap-2 flex-wrap",
								children: [/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-extrabold text-[17px] text-[#0f2a4a]",
									children: e.id
								}), /* @__PURE__ */ (0, R.jsx)(q, {
									tone: "blue",
									size: "sm",
									children: e.kind || "—"
								})]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[14.5px] mt-1",
								children: e.client || "—"
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									e.company || "—",
									" · ",
									e.agent || "—"
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-extrabold text-[16px] mt-1.5",
								children: W(e.value, e.currency)
							})
						]
					}), /* @__PURE__ */ (0, R.jsx)("div", {
						className: "border-t",
						children: /* @__PURE__ */ (0, R.jsxs)(L, {
							to: Yn(e.id),
							className: "touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]",
							children: ["MỞ HỢP ĐỒNG ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 17 })]
						})
					})]
				}, e.id)), s.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "font-bold text-[16px]",
						children: "Không tìm thấy hợp đồng nào"
					}), /* @__PURE__ */ (0, R.jsxs)(L, {
						to: "/hop-dong/moi",
						className: "btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center",
						children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 17 }), " Tạo hợp đồng"]
					})]
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/ContractDetail.tsx
var Rs = [
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
], zs = {
	READY: "green",
	GENERATED: "blue",
	MISSING_INFO: "amber",
	NOT_APPLICABLE: "gray",
	OWNER_RULE_REQUIRED: "amber",
	BLOCKED: "red",
	DEFERRED: "gray",
	ISSUED: "green"
}, Bs = {
	READY: "Sẵn sàng",
	GENERATED: "Đã sinh",
	MISSING_INFO: "Thiếu thông tin",
	NOT_APPLICABLE: "Không áp dụng",
	OWNER_RULE_REQUIRED: "Cần quy tắc chủ",
	BLOCKED: "Bị chặn",
	DEFERRED: "Hoãn lại",
	ISSUED: "Đã phát hành"
};
function Vs(e) {
	return {
		description: e.description,
		unit: e.unit,
		quantity: e.quantity == null ? "" : String(e.quantity),
		unitPrice: e.unitPrice == null ? "" : String(e.unitPrice)
	};
}
function Hs() {
	let { pathname: e } = gt(), t;
	try {
		t = decodeURIComponent(e.slice(10));
	} catch {
		t = void 0;
	}
	let [n, r] = Rn(), i = n.get("tab") || "tong-quan", { contracts: a, authority: o, shipments: s, customers: c, dispatch: l, toast: u } = Jn(), d = yt(), f = a.find((e) => e.id === t), [p, m] = (0, _.useState)({}), [h, g] = (0, _.useState)([]), [v, y] = (0, _.useState)(""), b = (e) => {
		m({
			company_id: e.companyId ?? "",
			agent_id: e.agentId ?? "",
			customerId: e.customerId ?? "",
			kind: e.kind ?? "",
			value: e.value == null ? "" : String(e.value),
			currency: e.currency || "VND",
			note: e.note ?? "",
			date: e.contractDate ?? "",
			pl_required: e.plRequired ?? "",
			hdnt_no: e.identity?.hdntNo ?? "",
			hdnt_date: e.identity?.hdntDate ?? "",
			valid_from: e.identity?.validFrom ?? "",
			valid_to: e.identity?.validTo ?? "",
			pl_no: e.identity?.plNo ?? "",
			pl_date: e.identity?.plDate ?? "",
			hdmb_no: e.identity?.hdmbNo ?? "",
			hdmb_date: e.identity?.hdmbDate ?? ""
		}), g(e.goodsLines.length ? e.goodsLines.map(Vs) : [{
			description: "",
			unit: "",
			quantity: "",
			unitPrice: ""
		}]);
	};
	if ((0, _.useEffect)(() => {
		f && b(f);
	}, [f?.id]), !f) return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-2xl bg-white border p-10 text-center max-w-[600px] mx-auto",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "font-extrabold text-[19px]",
				children: ["Không tìm thấy hợp đồng ", t]
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-slate-500 mt-1 text-[15px]",
				children: "Số hợp đồng có thể sai. Về danh sách để tìm lại."
			}),
			/* @__PURE__ */ (0, R.jsx)(L, {
				to: "/hop-dong",
				className: "btn-press touch-target mt-4 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[48px] items-center",
				children: "Về danh sách hợp đồng"
			})
		]
	});
	let x = (e, t) => m((n) => ({
		...n,
		[e]: t
	})), S = (e, t, n) => g((r) => r.map((r, i) => i === e ? {
		...r,
		[t]: n
	} : r)), C = () => g((e) => [...e, {
		description: "",
		unit: "",
		quantity: "",
		unitPrice: ""
	}]), w = (e) => g((t) => t.length > 1 ? t.filter((t, n) => n !== e) : t), T = () => {
		let e = (p.customerId ?? "").trim(), t = {
			id: f.id,
			company_id: p.company_id.trim(),
			agent_id: p.agent_id.trim(),
			kind: p.kind.trim(),
			currency: p.currency.trim(),
			note: p.note.trim(),
			value: p.value.trim(),
			date: (p.date ?? "").trim(),
			pl_required: (p.pl_required ?? "").trim(),
			hdnt_no: p.hdnt_no.trim(),
			hdnt_date: p.hdnt_date.trim(),
			valid_from: p.valid_from.trim(),
			valid_to: p.valid_to.trim(),
			pl_no: p.pl_no.trim(),
			pl_date: p.pl_date.trim(),
			hdmb_no: p.hdmb_no.trim(),
			hdmb_date: p.hdmb_date.trim()
		};
		if (e !== (f.customerId ?? "") && (t.customerId = e), !l("contract_save", t)) {
			u("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		u("Đã gửi lưu " + f.id, "Chờ máy chủ xử lý; dữ liệu sẽ được đọc lại từ Logistics.", "blue");
	}, E = () => {
		let e = h.map((e) => ({
			description: e.description.trim(),
			unit: e.unit.trim(),
			quantity: e.quantity.trim(),
			unitPrice: e.unitPrice.trim()
		}));
		if (!l("contract_goods_save", {
			id: f.id,
			goodsLines: e
		})) {
			u("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		u("Đã gửi lưu hàng hóa " + f.id, "Blank số lượng/đơn giá = UNKNOWN (không bao giờ thành 0).", "blue");
	}, D = () => {
		if (!l("contract_docgen_generate", { id: f.id })) {
			u("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		u("Đã gửi sinh chứng từ " + f.id, "core.docgen kiểm tra threshold 50 triệu & danh tính pháp lý rồi sinh Office thật.", "blue");
	}, O = (e, t) => {
		if (!l("contract_docgen_issue", {
			documentId: e,
			revision: t
		})) {
			u("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		u("Đã gửi phát hành " + e, "Chứng từ ISSUED sẽ bất biến (không sửa/xóa).", "blue");
	}, k = () => {
		let e = v.trim().toUpperCase();
		if (!e) {
			u("Thiếu mã lô", "Nhập mã lô để liên kết (VD: LO-0306).", "red");
			return;
		}
		if (!l("contract_shipment_link", {
			id: f.id,
			shipmentId: e
		})) {
			u("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		u("Đã gửi liên kết " + e, "Chờ máy chủ xử lý liên kết N:M hợp đồng ↔ lô.", "blue"), y("");
	};
	f.goodsTotals?.total_after_vat;
	let A = f.thresholdVnd ?? 5e7, ee = f.goodsTotals != null && f.goodsTotals.total_after_vat < A, j = s.filter((e) => !f.linkedShipments.some((t) => t.id === e.id));
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("button", {
				onClick: () => d(-1),
				className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
				children: [/* @__PURE__ */ (0, R.jsx)(mr, { size: 17 }), " Quay lại"]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 overflow-hidden",
				children: [
					/* @__PURE__ */ (0, R.jsx)("div", { className: "h-1.5 bg-gradient-to-r from-[#0f2a4a] via-[#1e5aa8] to-emerald-500" }),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "p-4 md:p-6",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "flex flex-wrap items-center gap-2",
								children: [
									/* @__PURE__ */ (0, R.jsx)("h1", {
										className: "text-[22px] md:text-[26px] font-extrabold text-[#0f2a4a]",
										children: f.id
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: "blue",
										size: "sm",
										children: f.kind || "—"
									}),
									/* @__PURE__ */ (0, R.jsx)(q, {
										tone: f.statusTone,
										size: "sm",
										children: f.status
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-semibold text-[15.5px] mt-1",
								children: f.client || "—"
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-2 md:grid-cols-4 gap-x-6 mt-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Công ty bên mua",
										value: K(f.company)
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Đại lý (bán)",
										value: K(f.agent)
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Giá trị",
										value: ho(f.value)
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Số lô liên kết",
										value: String(f.linkedShipments.length)
									})
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid grid-cols-2 md:grid-cols-4 gap-x-6 mt-1",
								children: [
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Khách hàng / đối tác",
										value: K(f.client)
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Ngày hợp đồng",
										value: K(f.contractDate)
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Phụ lục (PL)",
										value: f.plRequired === "YES" ? "Có PL" : f.plRequired === "NO" ? "Không cần PL" : "Chưa chọn"
									}),
									/* @__PURE__ */ (0, R.jsx)(Ao, {
										label: "Loại",
										value: K(f.kind)
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						id: "contract-tabs",
						className: "px-3 md:px-6 pb-3 flex gap-2 overflow-x-auto no-scrollbar border-t border-slate-100 pt-3",
						children: Rs.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: () => r({ tab: e.id }),
							className: U("touch-target shrink-0 rounded-xl px-4 min-h-[48px] text-[14.5px] font-bold border-2 whitespace-nowrap", i === e.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-600"),
							children: [/* @__PURE__ */ (0, R.jsx)("span", {
								className: "hidden md:inline",
								children: e.label
							}), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "md:hidden",
								children: e.short
							})]
						}, e.id))
					})
				]
			}),
			i === "tong-quan" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3",
					children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
						children: [/* @__PURE__ */ (0, R.jsx)(wi, {
							size: 19,
							className: "text-[#1e5aa8]"
						}), " Danh tính pháp lý"]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid sm:grid-cols-2 gap-3",
						children: [
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Số HDNT",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.hdnt_no,
									onChange: (e) => x("hdnt_no", e.target.value),
									placeholder: "HDNT-…/2026",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ngày HDNT",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.hdnt_date,
									onChange: (e) => x("hdnt_date", e.target.value),
									placeholder: "2026-09-01",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Hiệu lực từ",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.valid_from,
									onChange: (e) => x("valid_from", e.target.value),
									placeholder: "2026-09-01",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Hiệu lực đến",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.valid_to,
									onChange: (e) => x("valid_to", e.target.value),
									placeholder: "2027-08-31",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Số PL",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.pl_no,
									onChange: (e) => x("pl_no", e.target.value),
									placeholder: "PL-…/2026",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ngày PL",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.pl_date,
									onChange: (e) => x("pl_date", e.target.value),
									placeholder: "2026-09-02",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Số HDMB",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.hdmb_no,
									onChange: (e) => x("hdmb_no", e.target.value),
									placeholder: "HDMB-…/2026",
									className: X()
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ngày HDMB",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: p.hdmb_date,
									onChange: (e) => x("hdmb_date", e.target.value),
									placeholder: "2026-09-03",
									className: X()
								})
							})
						]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-3",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
							children: [/* @__PURE__ */ (0, R.jsx)(wr, {
								size: 19,
								className: "text-[#1e5aa8]"
							}), " Đối tác & thông tin chung"]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)(jo, {
									label: "Công ty bên mua",
									testId: "contract-buyer-picker",
									required: !0,
									options: o.companies.map((e) => ({
										id: e.id,
										label: e.legalName || e.id,
										sub: e.legalCode ? `MST ${e.legalCode} · ${e.id}` : e.id
									})),
									selectedId: p.company_id,
									selectedLabel: o.companies.find((e) => e.id === p.company_id)?.legalName ?? "",
									placeholder: "Gõ tên công ty hoặc MST để tìm…",
									emptyHint: "Chưa có hồ sơ pháp lý Công ty trong master — bổ sung ở màn Hồ sơ đại lý / Công ty trước.",
									onSelect: (e) => x("company_id", e)
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Đại lý (bên bán)",
									required: !0,
									children: /* @__PURE__ */ (0, R.jsxs)("select", {
										value: p.agent_id,
										onChange: (e) => x("agent_id", e.target.value),
										className: X(p.agent_id ? "ok" : "missing"),
										children: [/* @__PURE__ */ (0, R.jsx)("option", {
											value: "",
											children: "-- Chọn đại lý --"
										}), o.agents.map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
											value: e.id,
											children: e.legalName
										}, e.id))]
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(jo, {
									label: "Khách hàng / đối tác",
									testId: "contract-customer-picker",
									options: c.map((e) => ({
										id: e.id,
										label: e.name || e.id,
										sub: e.mst || e.taxCode ? `MST ${e.mst || e.taxCode} · ${e.id}` : e.id
									})),
									selectedId: p.customerId,
									selectedLabel: c.find((e) => e.id === p.customerId)?.name ?? "",
									placeholder: "Gõ tên khách hoặc mã khách để tìm…",
									emptyHint: "Danh bạ khách hàng đang trống — nhập từ GetFly ở màn Tạo hợp đồng.",
									onSelect: (e) => x("customerId", e)
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Ngày hợp đồng",
									hint: "2026-09-05 · để trống = chưa có ngày.",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.date ?? "",
										onChange: (e) => x("date", e.target.value),
										placeholder: "2026-09-05",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "sm:col-span-2 rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, R.jsx)(Mo, {
										testId: "contract-pl-choice",
										value: p.pl_required ?? "",
										onChange: (e) => x("pl_required", e),
										stored: f.plRequired === "YES" ? "Có PL" : f.plRequired === "NO" ? "Không cần PL" : "chưa chọn"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12.5px] text-slate-500 mt-1.5",
										children: "Bấm một trong hai ô rồi LƯU TỔNG QUAN: lựa chọn được ghi vào hợp đồng và đọc lại đúng nguyên văn. Để nguyên “Chưa chọn” khi chưa có quyết định — app không tự điền."
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Loại",
									children: /* @__PURE__ */ (0, R.jsxs)("select", {
										value: p.kind,
										onChange: (e) => x("kind", e.target.value),
										className: X(),
										children: [
											/* @__PURE__ */ (0, R.jsx)("option", {
												value: "HDMB",
												children: "HDMB"
											}),
											/* @__PURE__ */ (0, R.jsx)("option", {
												value: "HDNT",
												children: "HDNT"
											}),
											/* @__PURE__ */ (0, R.jsx)("option", {
												value: "PL",
												children: "PL"
											})
										]
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Giá trị (VND)",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.value,
										onChange: (e) => x("value", e.target.value),
										inputMode: "numeric",
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Tiền tệ",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.currency,
										onChange: (e) => x("currency", e.target.value),
										className: X()
									})
								}),
								/* @__PURE__ */ (0, R.jsx)(Y, {
									label: "Ghi chú",
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: p.note,
										onChange: (e) => x("note", e.target.value),
										className: X()
									})
								})
							]
						}),
						f.parties && (f.parties.company || f.parties.agent) && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3 pt-1",
							children: [f.parties.company && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-slate-50 border p-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] font-bold uppercase text-slate-400",
										children: "Công ty — hồ sơ pháp lý"
									}),
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-bold text-[14px] mt-1",
										children: f.parties.company.legalName
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											f.parties.company.legalCode,
											" · ",
											f.parties.company.legalAddress
										]
									})
								]
							}), f.parties.agent && /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl bg-slate-50 border p-3",
								children: [
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] font-bold uppercase text-slate-400",
										children: "Đại lý — hồ sơ pháp lý"
									}),
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-bold text-[14px] mt-1",
										children: f.parties.agent.legalName
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											f.parties.agent.legalCode,
											" · ",
											f.parties.agent.legalAddress
										]
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)(wo, {
							onClick: T,
							className: "w-full",
							children: "💾 LƯU TỔNG QUAN"
						})
					]
				})]
			}),
			i === "hang-hoa" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center justify-between mb-3",
							children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)(ra, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Hàng hóa hợp đồng"]
							}), /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: C,
								className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]",
								children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 15 }), " Thêm dòng"]
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "overflow-x-auto -mx-1",
							children: /* @__PURE__ */ (0, R.jsxs)("table", {
								className: "tbl w-full text-[14px] min-w-[720px]",
								children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, R.jsx)("th", {
										className: "w-10",
										children: "STT"
									}),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Mô tả hàng hóa" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Đơn vị" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Số lượng" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Đơn giá (VND)" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "VAT" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Thành tiền" }),
									/* @__PURE__ */ (0, R.jsx)("th", {})
								] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: h.map((e, t) => {
									let n = e.quantity.trim() === "" ? null : Number(e.quantity), r = e.unitPrice.trim() === "" ? null : Number(e.unitPrice), i = n != null && r != null ? n * r : null;
									return /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-bold text-slate-400",
											children: t + 1
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: e.description,
											onChange: (e) => S(t, "description", e.target.value),
											placeholder: "Mô tả hàng hóa",
											className: X()
										}) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: e.unit,
											onChange: (e) => S(t, "unit", e.target.value),
											placeholder: "Bộ / chiếc",
											className: X()
										}) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: e.quantity,
											onChange: (e) => S(t, "quantity", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: X()
										}) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("input", {
											value: e.unitPrice,
											onChange: (e) => S(t, "unitPrice", e.target.value),
											inputMode: "numeric",
											placeholder: "—",
											className: X()
										}) }),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "text-slate-600",
											children: "8%"
										}),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-bold whitespace-nowrap",
											children: mo(i) ? "—" : W(i)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)("button", {
											onClick: () => w(t),
											className: "touch-target inline-flex items-center justify-center w-9 h-9 rounded-lg text-red-600 hover:bg-red-50",
											"aria-label": "Xóa dòng",
											children: /* @__PURE__ */ (0, R.jsx)(Ua, { size: 16 })
										}) })
									] }, t);
								}) })]
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(wo, {
							onClick: E,
							className: "w-full mt-3",
							children: "💾 LƯU HÀNG HÓA"
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-2",
							children: "Số lượng / đơn giá để trống = UNKNOWN (“—”), không bao giờ tự thành 0. Dòng trống hoàn toàn sẽ bị bỏ qua."
						})
					]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
							children: "Tổng & quyết định chứng từ (backend)"
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid grid-cols-2 md:grid-cols-4 gap-3 text-center",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] text-slate-500 font-semibold",
										children: "Tổng trước thuế"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[17px]",
										children: W(f.goodsTotals?.subtotal)
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border p-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] text-slate-500 font-semibold",
										children: "VAT 8%"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[17px]",
										children: W(f.goodsTotals?.vat_amount)
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-blue-50 border border-blue-200 p-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] text-blue-700 font-semibold",
										children: "Sau thuế"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[17px] text-blue-700",
										children: W(f.goodsTotals?.total_after_vat)
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-violet-50 border border-violet-200 p-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] text-violet-700 font-semibold",
										children: "Ngưỡng"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[17px] text-violet-700",
										children: W(A)
									})]
								})
							]
						}),
						f.goodsTotals == null ? /* @__PURE__ */ (0, R.jsx)("div", {
							className: "mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13.5px] text-amber-900",
							children: "Chưa có tổng đáng tin cậy (có dòng UNKNOWN) — không thể thay bằng 0, chứng từ bị chặn cho tới khi đủ dữ liệu."
						}) : /* @__PURE__ */ (0, R.jsxs)("div", {
							className: U("mt-3 rounded-xl border-2 p-3.5", ee ? "border-emerald-300 bg-emerald-50" : "border-blue-300 bg-blue-50"),
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "font-extrabold text-[15px]",
								children: ee ? "Sau thuế < 50.000.000 ₫ → HDNT + PL" : "Sau thuế ≥ 50.000.000 ₫ → HDMB"
							}), /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13.5px] mt-0.5",
								children: ["Áp dụng: ", /* @__PURE__ */ (0, R.jsx)("b", { children: f.applicableDocuments.length ? f.applicableDocuments.join(" + ") : "—" })]
							})]
						})
					]
				})]
			}),
			i === "chung-tu" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center justify-between mb-3",
							children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
								className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2",
								children: [/* @__PURE__ */ (0, R.jsx)(gi, {
									size: 19,
									className: "text-[#1e5aa8]"
								}), " Chứng từ HDNT · PL · HDMB"]
							}), /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: D,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]",
								children: [/* @__PURE__ */ (0, R.jsx)(za, { size: 17 }), " SINH CHỨNG TỪ"]
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-slate-500 mb-3",
							children: "Quy tắc backend: VAT 8% · VND · làm tròn nửa lên từng đồng · sau thuế < 50M → HDNT + PL, ≥ 50M → HDMB. Chỉ sinh khi READY."
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid sm:grid-cols-2 gap-2.5",
							children: f.docCards.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-xl border-2 p-3.5",
								style: { borderColor: "var(--slate-200)" },
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex items-center justify-between gap-2",
										children: [/* @__PURE__ */ (0, R.jsx)("span", {
											className: "font-extrabold text-[14.5px] text-[#0f2a4a]",
											children: e.document_type
										}), /* @__PURE__ */ (0, R.jsx)(q, {
											tone: zs[e.state] ?? "gray",
											size: "sm",
											children: Bs[e.state] ?? e.state
										})]
									}),
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[13px] text-slate-600 mt-1",
										children: e.reason
									}),
									e.missing.length > 0 && /* @__PURE__ */ (0, R.jsx)("ul", {
										className: "mt-1.5 text-[12.5px] text-amber-800 list-disc pl-4 space-y-0.5",
										children: e.missing.map((e) => /* @__PURE__ */ (0, R.jsx)("li", { children: e }, e))
									})
								]
							}, e.document_type))
						})
					]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
						children: "Chứng từ đã sinh — tải về / phát hành / lịch sử"
					}), f.documents.length === 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Chưa có chứng từ nào. Nhập hàng hóa rồi bấm “SINH CHỨNG TỪ”."
					}) : /* @__PURE__ */ (0, R.jsx)("div", {
						className: "space-y-2",
						children: f.documents.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2.5 rounded-xl border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: U("w-9 h-9 rounded-lg grid place-items-center shrink-0", e.status === "ISSUED" ? "bg-emerald-600 text-white" : "bg-blue-100 text-blue-700"),
									children: e.status === "ISSUED" ? /* @__PURE__ */ (0, R.jsx)(Kr, { size: 18 }) : /* @__PURE__ */ (0, R.jsx)(wi, { size: 18 })
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex-1 min-w-[180px]",
									children: [/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "font-bold text-[14.5px] text-[#0f2a4a]",
										children: [
											e.documentTypeLabel,
											" · R",
											e.revision
										]
									}), /* @__PURE__ */ (0, R.jsxs)("p", {
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
								e.downloadAvailable && e.downloadBase64 && /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => xo(e.fileName, e.downloadBase64, e.mime),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, R.jsx)(ci, { size: 16 }), " Tải"]
								}),
								e.status !== "ISSUED" && /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => O(e.documentId, e.revision),
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 text-white font-bold text-[13.5px] px-3 min-h-[44px]",
									children: [/* @__PURE__ */ (0, R.jsx)(za, { size: 15 }), " Phát hành"]
								}),
								e.status === "ISSUED" && /* @__PURE__ */ (0, R.jsx)(q, {
									tone: "green",
									size: "sm",
									children: "ISSUED — bất biến"
								})
							]
						}, e.id))
					})]
				})]
			}),
			i === "lo-lien-ket" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid grid-cols-1 xl:grid-cols-2 gap-4",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, R.jsxs)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2 mb-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Li, {
							size: 19,
							className: "text-[#1e5aa8]"
						}), " Lô hàng liên kết"]
					}), f.linkedShipments.length === 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Chưa liên kết lô nào."
					}) : /* @__PURE__ */ (0, R.jsx)("div", {
						className: "space-y-2",
						children: f.linkedShipments.map((e) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center gap-2.5 rounded-xl border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "w-9 h-9 rounded-lg bg-blue-100 text-blue-700 grid place-items-center",
									children: /* @__PURE__ */ (0, R.jsx)(ra, { size: 18 })
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex-1 min-w-0",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-bold text-[14.5px] text-[#0f2a4a]",
										children: e.id
									}), /* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[12.5px] text-slate-500",
										children: [
											e.customer,
											" · ",
											e.status
										]
									})]
								}),
								/* @__PURE__ */ (0, R.jsxs)(L, {
									to: e.to,
									className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]",
									children: ["MỞ ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 15 })]
								})
							]
						}, e.id))
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] mb-3",
						children: "Liên kết lô mới"
					}), j.length === 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500",
						children: "Tất cả lô đã được liên kết."
					}) : /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3",
						children: [/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Chọn lô hàng",
							required: !0,
							children: /* @__PURE__ */ (0, R.jsxs)("select", {
								value: v,
								onChange: (e) => y(e.target.value),
								className: X(v ? "ok" : "missing"),
								children: [/* @__PURE__ */ (0, R.jsx)("option", {
									value: "",
									children: "-- Chọn lô --"
								}), j.map((e) => /* @__PURE__ */ (0, R.jsxs)("option", {
									value: e.id,
									children: [
										e.id,
										" · ",
										e.customer
									]
								}, e.id))]
							})
						}), /* @__PURE__ */ (0, R.jsx)(wo, {
							onClick: k,
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
var Us = "Mã ĐH	Ngày đặt hàng	Tên KH	Mã KH\nDH-1001	05/09/2026	An Phát JSC	CUST-ANPHAT";
function Ws() {
	let { customers: e, dispatch: t, toast: n } = Jn(), r = (0, _.useSyncExternalStore)(C, S, S), i = yt(), a = (0, _.useRef)(null), [o, s] = (0, _.useState)(null), [c, l] = (0, _.useState)("");
	(0, _.useEffect)(() => {
		if (!o || a.current !== o) return;
		let e = r?.lastWrites?.find((e) => e.event === "contract_create" && e.requestId === o.requestId);
		e && (e.ok === !1 ? (a.current = null, s(null), l(String(e.error || "Máy chủ từ chối tạo hợp đồng."))) : e.ok === !0 && r?.contracts.some((e) => e.id === o.id) && (a.current = null, s(null), i(Yn(o.id))));
	}, [
		r,
		o,
		i
	]);
	let [u, d] = (0, _.useState)(""), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)("HDMB"), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)(""), [x, w] = (0, _.useState)(""), [T, E] = (0, _.useState)(!1), [D, O] = (0, _.useState)(""), [k, A] = (0, _.useState)(""), ee = (0, _.useMemo)(() => e.map((e) => ({
		id: e.id,
		label: e.name || e.id,
		sub: e.mst || e.taxCode ? `MST ${e.mst || e.taxCode} · ${e.id}` : e.id
	})), [e]), j = e.find((e) => e.id === f) ?? null, M = (0, _.useMemo)(() => k ? (r?.lastWrites ?? []).find((e) => e.event === "customer_getfly_import" && e.requestId === k) ?? null : null, [r?.lastWrites, k]), N = () => {
		let e = D.trim();
		if (!e) {
			n("Chưa có gì để nhập", "Dán các dòng đơn hàng từ file GetFly (kèm dòng tiêu đề).", "red");
			return;
		}
		let r = `GETFLY-${Date.now().toString(36).toUpperCase()}`;
		if (!t("customer_getfly_import", {
			text: e,
			requestId: r
		})) {
			n("Không gửi được", "Component chưa kết nối backend.", "red");
			return;
		}
		A(r), n("Đã gửi dữ liệu GetFly", "Máy chủ đọc cột GetFly, ghi khách hàng mới rồi báo lại kết quả.", "blue");
	}, te = () => {
		if (a.current) return;
		let e = u.trim().toUpperCase();
		if (!e) {
			n("Thiếu số hợp đồng", "Nhập số hợp đồng (VD: HDMB-0310).", "red");
			return;
		}
		if (!f) {
			n("Chưa chọn khách hàng", "Bấm “Tìm / đổi” rồi chọn khách hàng / đối tác.", "red");
			return;
		}
		let r = {
			id: e,
			requestId: crypto.randomUUID()
		};
		a.current = r, s(r), l(""), t("contract_create", {
			requestId: r.requestId,
			id: e,
			customerId: f,
			kind: m,
			note: g.trim(),
			date: y.trim(),
			pl_required: x
		}) || (a.current = null, s(null), l("Không gửi được. Component chưa kết nối backend."));
	}, P = M?.customers ?? [], F = M?.skippedMissing ?? [], ne = M?.orders ?? [];
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[760px]",
		children: [/* @__PURE__ */ (0, R.jsxs)("button", {
			onClick: () => i(-1),
			className: "touch-target inline-flex items-center gap-1.5 text-[14.5px] font-bold text-slate-500 hover:text-[#0f2a4a]",
			children: [/* @__PURE__ */ (0, R.jsx)(mr, { size: 17 }), " Quay lại"]
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-6",
			children: [
				/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(wi, { size: 18 }),
					title: "Tạo hợp đồng mới",
					sub: "HDMB / HDNT + Phụ lục — sau khi tạo sẽ nhập hàng hóa, sinh chứng từ và liên kết lô"
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid sm:grid-cols-2 gap-3",
					children: [/* @__PURE__ */ (0, R.jsx)(Y, {
						label: "Số hợp đồng",
						required: !0,
						error: u ? void 0 : "Nhập số hợp đồng",
						children: /* @__PURE__ */ (0, R.jsx)("input", {
							value: u,
							onChange: (e) => d(e.target.value),
							placeholder: "VD: HDMB-0310",
							className: X(u ? "ok" : "missing")
						})
					}), /* @__PURE__ */ (0, R.jsx)(Y, {
						label: "Loại hợp đồng",
						required: !0,
						children: /* @__PURE__ */ (0, R.jsxs)("select", {
							value: m,
							onChange: (e) => h(e.target.value),
							className: X(),
							children: [
								/* @__PURE__ */ (0, R.jsx)("option", {
									value: "HDMB",
									children: "HDMB — Hợp đồng mua bán (≥ 50 triệu)"
								}),
								/* @__PURE__ */ (0, R.jsx)("option", {
									value: "HDNT",
									children: "HDNT — Hợp đồng nguyên tắc (< 50 triệu)"
								}),
								/* @__PURE__ */ (0, R.jsx)("option", {
									value: "PL",
									children: "PL — Phụ lục hợp đồng"
								})
							]
						})
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid gap-3 mt-3",
					children: [
						/* @__PURE__ */ (0, R.jsx)(jo, {
							label: "Khách hàng / đối tác",
							testId: "contract-customer-picker",
							required: !0,
							options: ee,
							selectedId: f,
							selectedLabel: j ? `${j.name} (${j.id})` : "",
							placeholder: "Gõ tên khách hoặc mã khách (VD: An Phát, CUST-ANPHAT)…",
							emptyHint: "Danh bạ khách hàng đang trống — nhập từ GetFly bên dưới hoặc tạo mới ở mục Khách Hàng.",
							onSelect: p
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid sm:grid-cols-2 gap-3",
							children: [/* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ngày hợp đồng",
								hint: "Định dạng 2026-09-05 — để trống nếu chưa có.",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: y,
									onChange: (e) => b(e.target.value),
									placeholder: "2026-09-05",
									className: X()
								})
							}), /* @__PURE__ */ (0, R.jsx)(Y, {
								label: "Ghi chú",
								children: /* @__PURE__ */ (0, R.jsx)("input", {
									value: g,
									onChange: (e) => v(e.target.value),
									placeholder: "Ghi chú nội bộ",
									className: X()
								})
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl border border-slate-200 p-3",
							children: [/* @__PURE__ */ (0, R.jsx)(Mo, {
								testId: "contract-pl-choice",
								value: x,
								onChange: w
							}), /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12.5px] text-slate-500 mt-1.5",
								children: "Đây là quyết định của bộ phận vận hành ghi trên hợp đồng; quy tắc 50 triệu của chứng từ (HDNT + PL hay HDMB) vẫn do máy chủ tính, không đổi theo ô chọn này."
							})]
						})
					]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-4 rounded-xl bg-slate-50 border border-slate-200 p-3",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-center justify-between gap-2",
							children: [/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[14px] font-extrabold text-[#0f2a4a] flex items-center gap-1.5",
								children: [/* @__PURE__ */ (0, R.jsx)(Qr, { size: 16 }), " Nhập khách hàng từ GetFly (DSDH)"]
							}), /* @__PURE__ */ (0, R.jsx)("button", {
								type: "button",
								onClick: () => E((e) => !e),
								"aria-expanded": T,
								className: "btn-press touch-target rounded-lg border-2 border-slate-200 bg-white px-3 min-h-[36px] text-[13px] font-bold text-slate-600",
								"data-testid": "contract-getfly-toggle",
								children: T ? "Đóng" : "Dán dữ liệu GetFly"
							})]
						}),
						T && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-2.5 space-y-2",
							"data-testid": "contract-getfly-panel",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12.5px] text-slate-500",
									children: "Copy nguyên khối trong file GetFly (bao gồm dòng tiêu đề: Mã ĐH · Ngày đặt hàng · Tên KH · Mã KH). GetFly chỉ mang theo khách hàng và đơn hàng — mã hợp đồng, hồ sơ pháp lý Công ty (bên mua) và MST không có trong sheet đó nên app không tự đặt."
								}),
								/* @__PURE__ */ (0, R.jsx)("textarea", {
									value: D,
									onChange: (e) => O(e.target.value),
									rows: 5,
									placeholder: Us,
									className: X() + " font-mono text-[13px]",
									"data-testid": "contract-getfly-text"
								}),
								/* @__PURE__ */ (0, R.jsx)("div", {
									className: "flex flex-wrap gap-2",
									children: /* @__PURE__ */ (0, R.jsx)(Eo, {
										onClick: N,
										className: "flex-1",
										children: "📥 Nhập khách hàng từ GetFly"
									})
								})
							]
						}),
						M && /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-lg px-2.5 py-2 text-[13px] font-semibold " + (M.ok ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"),
							"data-testid": "contract-getfly-outcome",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", { children: String(M.error || "Đã nhập khách hàng từ GetFly.") }),
								P.length > 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "mt-1 font-medium text-slate-600",
									children: [
										"Đã có trong danh bạ: ",
										P.map((e) => `${e.name} (${e.id})`).join(", "),
										ne.length > 0 ? ` · ${ne.length} đơn hàng GetFly` : null
									]
								}),
								F.length > 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "mt-1 font-medium text-amber-700",
									children: ["Bỏ qua (thiếu mã KH hoặc tên KH): ", F.join(", ")]
								}),
								M.ok && P.length > 0 && /* @__PURE__ */ (0, R.jsx)("div", {
									className: "mt-1.5 flex flex-wrap gap-1.5",
									children: P.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
										type: "button",
										onClick: () => p(e.id),
										className: "btn-press touch-target rounded-lg border-2 border-emerald-300 bg-white px-2.5 min-h-[34px] text-[12.5px] font-bold text-emerald-800",
										"data-testid": `contract-getfly-use-${e.id}`,
										children: [
											"Dùng ",
											e.name,
											" cho hợp đồng này"
										]
									}, e.id))
								})
							]
						})
					]
				}),
				c && /* @__PURE__ */ (0, R.jsx)("p", {
					role: "alert",
					className: "mt-4 text-red-700",
					"data-testid": "contract-create-error",
					children: c
				}),
				o && /* @__PURE__ */ (0, R.jsx)("p", {
					role: "status",
					className: "mt-4 text-slate-600",
					"data-testid": "contract-create-pending",
					children: "Đang chờ kết quả và dữ liệu hợp đồng từ máy chủ… Không gửi lại yêu cầu."
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid grid-cols-2 gap-2.5 mt-5",
					children: [/* @__PURE__ */ (0, R.jsx)(Eo, {
						onClick: () => i(-1),
						children: "Hủy"
					}), /* @__PURE__ */ (0, R.jsx)(wo, {
						onClick: te,
						disabled: !!o,
						children: "💾 TẠO HỢP ĐỒNG"
					})]
				})
			]
		})]
	});
}
//#endregion
//#region src/pages/TariffLookup.tsx
function Gs(e) {
	return e || "—";
}
function Ks({ row: e, stacked: t }) {
	return e.fields.length ? /* @__PURE__ */ (0, R.jsx)("span", {
		className: U("text-[13.5px] text-slate-700", t && "block"),
		children: e.fields.map((e) => /* @__PURE__ */ (0, R.jsxs)("span", {
			className: U(!t && "mr-3 whitespace-nowrap"),
			children: [
				/* @__PURE__ */ (0, R.jsxs)("span", {
					className: "font-semibold text-slate-500",
					children: [e.label, ":"]
				}),
				" ",
				/* @__PURE__ */ (0, R.jsx)("span", {
					className: "font-bold",
					children: Gs(e.value)
				})
			]
		}, e.label))
	}) : /* @__PURE__ */ (0, R.jsx)("span", {
		className: "text-slate-400",
		children: "—"
	});
}
function qs() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.tariff ?? null, [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(""), a = r.length > 0 && r !== (e?.query ?? ""), o = e?.rows ?? [], s = !!e?.searched && !a, c = () => {
		let e = t.trim();
		e.length < 2 || (i(e), A("tariff_lookup", { query: e }));
	}, l = e?.source, u = e?.provenance;
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Ta, { size: 18 }),
						title: "Tra cứu HS & Thuế",
						sub: "Tra cứu mã HS và mô tả hàng hóa tại cơ sở dữ liệu tham chiếu nội bộ — nhập mã HS (chính xác hoặc một phần) hoặc tên hàng."
					}),
					/* @__PURE__ */ (0, R.jsxs)("form", {
						className: "flex flex-col md:flex-row gap-2.5",
						onSubmit: (e) => {
							e.preventDefault(), c();
						},
						children: [/* @__PURE__ */ (0, R.jsx)("input", {
							value: t,
							onChange: (e) => n(e.target.value),
							placeholder: "Ví dụ: 9401, 9403.20 hoặc ghế gỗ…",
							className: "flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] font-mono placeholder:font-sans focus:border-[#1e5aa8] outline-none",
							"aria-label": "Mã HS hoặc tên hàng"
						}), /* @__PURE__ */ (0, R.jsxs)("button", {
							type: "submit",
							disabled: t.trim().length < 2,
							className: "btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-40 disabled:pointer-events-none",
							children: [/* @__PURE__ */ (0, R.jsx)(Ta, { size: 17 }), " Tra cứu"]
						})]
					}),
					l && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: U("mt-3 rounded-xl border p-3 flex items-start gap-2.5 text-[13px]", l.configured && l.rows ? "border-slate-200 bg-slate-50 text-slate-600" : "border-amber-200 bg-amber-50 text-amber-900"),
						children: [/* @__PURE__ */ (0, R.jsx)(oi, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [l.configured && l.rows ? /* @__PURE__ */ (0, R.jsxs)("p", { children: [
							"Nguồn nội bộ: ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "tariff_table" }),
							" · ",
							l.rows.toLocaleString("vi-VN"),
							" dòng ·",
							" ",
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "font-mono text-[12px] break-all",
								children: l.path
							})
						] }) : /* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-semibold",
							children: l.note
						}), e?.truncated && /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "mt-1 font-semibold",
							children: [
								"Kết quả bị giới hạn ",
								e.limit,
								" dòng — hãy nhập mã HS cụ thể hơn."
							]
						})] })]
					}),
					u && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-2.5 rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/60 p-3 flex items-start gap-2.5 text-[13px] text-amber-900",
						children: [/* @__PURE__ */ (0, R.jsx)(Ga, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsx)("p", { children: u.note })]
					})
				]
			}),
			a && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: [
						"Đang tra cứu “",
						r,
						"”…"
					]
				})
			}),
			!a && !s && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Ta, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Bảng kết quả đang trống"
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: [
							"Nhập mã HS hoặc tên hàng phía trên rồi bấm ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "Tra cứu" }),
							"."
						]
					})
				]
			}),
			s && e && o.length === 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Ai, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Không tìm thấy kết quả"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: e.reason
					})
				]
			}),
			s && e && o.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "space-y-4",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13.5px] font-semibold text-slate-500 px-1",
						children: [
							"Tìm thấy ",
							e.count.toLocaleString("vi-VN"),
							" dòng khớp “",
							e.query,
							"” — mã HS và mô tả theo dữ liệu tham chiếu nội bộ."
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
						children: /* @__PURE__ */ (0, R.jsx)("div", {
							className: "overflow-x-auto",
							children: /* @__PURE__ */ (0, R.jsxs)("table", {
								className: "tbl w-full text-[14.5px]",
								children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, R.jsx)("th", {
										className: "w-[150px]",
										children: "Mã HS"
									}),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Mô tả tiếng Việt" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Mô tả tiếng Anh" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Thông tin khác (nguyên văn)" })
								] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: o.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("tr", {
									className: "hover:bg-slate-50",
									children: [
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-mono font-extrabold text-[15px] text-[#0f2a4a] whitespace-nowrap",
											children: Gs(e.hsCode)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-semibold",
											children: Gs(e.descriptionVi)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "text-slate-600",
											children: Gs(e.descriptionEn)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: /* @__PURE__ */ (0, R.jsx)(Ks, { row: e }) })
									]
								}, (e.hsCode ?? "?") + t)) })]
							})
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "md:hidden space-y-3",
						children: o.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl bg-white border border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "font-mono font-extrabold text-[17px] text-[#0f2a4a] break-all",
									children: Gs(e.hsCode)
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[15px] font-semibold text-slate-800 mt-1.5",
									children: Gs(e.descriptionVi)
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13px] text-slate-500 mt-0.5",
									children: Gs(e.descriptionEn)
								}),
								e.fields.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-2.5 rounded-xl bg-slate-50 border border-slate-200 p-3",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] font-bold uppercase tracking-wide text-slate-400",
										children: "Thông tin khác (nguyên văn)"
									}), /* @__PURE__ */ (0, R.jsx)("div", {
										className: "mt-1",
										children: /* @__PURE__ */ (0, R.jsx)(Ks, {
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
function Js(e) {
	return typeof TextEncoder < "u" ? new TextEncoder().encode(e).length : e.length;
}
function Ys(e, t, n) {
	return `${t}\u0000${n}\u0000${e}`;
}
var Xs = [
	{
		zh: "装箱单",
		hint: "Phiếu đóng gói (Packing List)"
	},
	{
		zh: "商业发票",
		hint: "Hóa đơn thương mại (Commercial Invoice)"
	},
	{
		zh: "提单",
		hint: "Vận đơn (Bill of Lading)"
	},
	{
		zh: "原产地证",
		hint: "Giấy chứng nhận xuất xứ (C/O)"
	}
];
function Zs({ label: e, value: t, options: n, onChange: r, disabled: i }) {
	return /* @__PURE__ */ (0, R.jsxs)("label", {
		className: "block flex-1 min-w-0",
		children: [/* @__PURE__ */ (0, R.jsx)("span", {
			className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
			children: e
		}), /* @__PURE__ */ (0, R.jsx)("select", {
			value: t,
			disabled: i,
			onChange: (e) => r(e.target.value),
			className: U(X(), "disabled:opacity-50"),
			"aria-label": e,
			children: n.map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
				value: e.code,
				children: e.label
			}, e.code))
		})]
	});
}
function Qs() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.translation ?? null, t = e?.capability ?? null, n = e?.request ?? null, r = e?.result ?? null, [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)("AUTO"), [c, l] = (0, _.useState)("VI"), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)("idle"), m = t?.maxTextBytes ?? 1e5, h = (0, _.useMemo)(() => Js(i), [i]), g = h > m, v = t?.configured ?? !1, y = t?.allowed ?? !1, b = n ? Ys(n.text, n.sourceLang, n.targetLang) : null, x = u !== null && u !== b, w = v && y && i.trim().length > 0 && !g && !x, T = r?.status === "translated" ? r.text ?? "" : "", E = () => {
		w && (p("idle"), d(Ys(i, o, c)), A("translate_text", {
			text: i,
			sourceLang: o,
			targetLang: c
		}));
	}, D = () => {
		if (!t) return;
		let e = t.swapSource[c], n = t.swapTarget[o];
		e && s(e), n && l(n);
	}, O = () => {
		a(""), d(null), p("idle");
	}, k = async () => {
		if (T) try {
			await navigator.clipboard.writeText(T), p("done");
		} catch {
			p("failed");
		}
	}, ee = t?.sourceLanguages ?? [], j = t?.targetLanguages ?? [], M = r && r.status !== "translated" ? r.error : null;
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1100px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(B, { size: 18 }),
						title: "Dịch thuật",
						sub: `Dịch văn bản nghiệp vụ logistics qua ${t?.provider ?? "nhà cung cấp dịch"} — nhập hoặc dán nội dung, chọn cặp ngôn ngữ rồi bấm Dịch.`
					}),
					t && !v && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mb-3 rounded-xl border border-amber-300 bg-amber-50 p-3 flex items-start gap-2.5 text-[13.5px] text-amber-900",
						children: [/* @__PURE__ */ (0, R.jsx)(Da, {
							size: 17,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-extrabold",
							children: "Translation service chưa được cấu hình"
						}), /* @__PURE__ */ (0, R.jsx)("p", {
							className: "mt-0.5",
							children: t.configNotice
						})] })]
					}),
					t && v && !y && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mb-3 rounded-xl border border-red-200 bg-red-50 p-3 flex items-start gap-2.5 text-[13.5px] text-red-800",
						children: [/* @__PURE__ */ (0, R.jsx)(Da, {
							size: 17,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "font-semibold",
							children: [
								"Vai trò hiện tại không có quyền dịch thuật (quyền ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: "translation" }),
								")."
							]
						})]
					}),
					t?.externalProvider && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mb-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-3 flex items-start gap-2.5 text-[13px] text-slate-600",
						children: [/* @__PURE__ */ (0, R.jsx)(Ai, {
							size: 16,
							className: "shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsx)("p", { children: t.privacyNotice })]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-col md:flex-row md:items-end gap-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsx)(Zs, {
								label: "Ngôn ngữ nguồn",
								value: o,
								options: ee,
								onChange: s
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "md:pb-1",
								children: /* @__PURE__ */ (0, R.jsxs)("button", {
									type: "button",
									onClick: D,
									"aria-label": "Đổi chiều dịch",
									title: "Đổi chiều dịch",
									className: "btn-press touch-target w-full md:w-auto inline-flex items-center justify-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-4 min-h-[48px] hover:bg-slate-50",
									children: [/* @__PURE__ */ (0, R.jsx)(fr, { size: 17 }), " Đổi chiều"]
								})
							}),
							/* @__PURE__ */ (0, R.jsx)(Zs, {
								label: "Ngôn ngữ đích",
								value: c,
								options: j,
								onChange: l
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "mt-3 flex flex-wrap gap-2",
						role: "group",
						"aria-label": "Cụm từ nhanh",
						children: Xs.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
							type: "button",
							onClick: () => {
								a(e.zh), d(null), p("idle");
							},
							title: e.hint,
							"aria-label": `${e.zh} — ${e.hint}`,
							className: "btn-press touch-target inline-flex items-center rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 text-[14.5px] font-semibold text-[#0f2a4a] min-h-[44px] hover:bg-slate-100 hover:border-slate-300",
							children: e.zh
						}, e.zh))
					}),
					/* @__PURE__ */ (0, R.jsxs)("label", {
						className: "block mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)("span", {
							className: "block text-[14px] font-semibold text-slate-700 mb-1.5",
							children: "Văn bản gốc"
						}), /* @__PURE__ */ (0, R.jsx)("textarea", {
							value: i,
							onChange: (e) => {
								a(e.target.value), d(null);
							},
							placeholder: "Dán nội dung cần dịch: email khách, mô tả hàng hóa, chứng từ…",
							"aria-label": "Văn bản gốc",
							className: "w-full rounded-xl border-2 border-slate-200 bg-white px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] focus:border-[#1e5aa8] outline-none resize-y"
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: U("mt-1 text-[13px]", g ? "text-red-700 font-semibold" : "text-slate-500"),
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
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-col sm:flex-row gap-2.5 mt-3",
						children: [/* @__PURE__ */ (0, R.jsx)(wo, {
							onClick: E,
							disabled: !w,
							className: "flex-1",
							children: x ? /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)(Ui, {
								size: 17,
								className: "animate-spin"
							}), " Đang dịch…"] }) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)(B, { size: 17 }), " Dịch"] })
						}), /* @__PURE__ */ (0, R.jsxs)(Eo, {
							onClick: O,
							className: "sm:w-auto",
							children: [/* @__PURE__ */ (0, R.jsx)(ui, { size: 17 }), " Xóa nội dung nhập"]
						})]
					})
				]
			}),
			x && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: [/* @__PURE__ */ (0, R.jsx)(Ui, {
					size: 24,
					className: "mx-auto animate-spin text-[#1e5aa8]"
				}), /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[15px] font-semibold text-slate-500 mt-2",
					children: [
						"Đang dịch qua ",
						t?.provider ?? "nhà cung cấp dịch",
						"…"
					]
				})]
			}),
			!x && M && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-2.5",
				children: [/* @__PURE__ */ (0, R.jsx)(Ga, {
					size: 18,
					className: "shrink-0 mt-0.5 text-red-600"
				}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[15px] font-extrabold text-red-800",
					children: r?.status === "config_required" ? "Translation service chưa được cấu hình" : "Chưa dịch được nội dung này"
				}), /* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[14px] text-red-700 mt-0.5",
					children: M
				})] })]
			}),
			!x && r?.status === "translated" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap items-center justify-between gap-2 mb-2",
						children: [/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "text-[16px] font-extrabold text-[#0f2a4a]",
							children: "Bản dịch"
						}), /* @__PURE__ */ (0, R.jsx)("div", {
							className: "flex flex-wrap gap-2",
							children: /* @__PURE__ */ (0, R.jsx)("button", {
								type: "button",
								onClick: k,
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px] hover:bg-slate-50",
								children: f === "done" ? /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)(Rr, {
									size: 16,
									className: "text-emerald-600"
								}), " Đã sao chép"] }) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)(ii, { size: 16 }), " Sao chép bản dịch"] })
							})
						})]
					}),
					f === "failed" && /* @__PURE__ */ (0, R.jsx)("p", {
						className: "mb-2 text-[13px] text-amber-800 font-semibold",
						children: "Trình duyệt không cho phép sao chép tự động — hãy bôi đen bản dịch rồi sao chép thủ công."
					}),
					/* @__PURE__ */ (0, R.jsx)("textarea", {
						readOnly: !0,
						value: T,
						"aria-label": "Bản dịch",
						className: "w-full rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] resize-y whitespace-pre-wrap"
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[13px] text-slate-500 mt-2",
						children: [
							"Ngôn ngữ nguồn phát hiện:",
							" ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: r.detectedSourceLanguage ?? "—" }),
							" · Ký tự tính phí:",
							" ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: r.billedCharacters === null ? "—" : r.billedCharacters.toLocaleString("vi-VN") }),
							" ",
							"· ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: r.apiLabel ?? "—" })
						]
					}),
					n && /* @__PURE__ */ (0, R.jsxs)("p", {
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
			!x && !r && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(B, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có bản dịch"
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: [
							"Nhập văn bản, chọn cặp ngôn ngữ rồi bấm ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "Dịch" }),
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
var $s = {
	agentId: "",
	legalName: "",
	legalCode: "",
	legalAddress: "",
	legalRepresentative: "",
	representativeTitle: "",
	phone: "",
	email: "",
	bankAccountHolder: "",
	bankAccountNumber: "",
	bankName: "",
	bankBranch: ""
}, ec = [
	{
		key: "agentId",
		label: "Mã đại lý",
		required: !0,
		lockedOnEdit: !0,
		mono: !0
	},
	{
		key: "legalName",
		label: "Tên pháp lý",
		required: !0,
		wide: !0
	},
	{
		key: "legalCode",
		label: "Mã số / mã pháp lý",
		mono: !0
	},
	{
		key: "legalAddress",
		label: "Địa chỉ",
		wide: !0
	},
	{
		key: "legalRepresentative",
		label: "Người đại diện"
	},
	{
		key: "representativeTitle",
		label: "Chức vụ"
	},
	{
		key: "phone",
		label: "Điện thoại",
		mono: !0
	},
	{
		key: "email",
		label: "Email"
	},
	{
		key: "bankAccountHolder",
		label: "Chủ tài khoản"
	},
	{
		key: "bankAccountNumber",
		label: "Số tài khoản",
		mono: !0
	},
	{
		key: "bankName",
		label: "Ngân hàng"
	},
	{
		key: "bankBranch",
		label: "Chi nhánh ngân hàng"
	}
], tc = {
	CONFIRMED: "blue",
	REVIEW_REQUIRED: "amber",
	KNOWN: "green",
	UNKNOWN: "gray"
}, nc = (e) => tc[(e ?? "").toUpperCase()] ?? "gray";
function rc({ label: e, value: t, mono: n }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-xl bg-slate-50 border border-slate-200 p-3",
		children: [/* @__PURE__ */ (0, R.jsx)("p", {
			className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
			children: e
		}), /* @__PURE__ */ (0, R.jsx)("p", {
			className: U("mt-0.5 font-semibold text-[14.5px] break-words", n && "font-mono"),
			children: K(t)
		})]
	});
}
function ic({ label: e, value: t, ccy: n, strong: r }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: U("rounded-xl border p-2.5 text-center", r ? "bg-amber-50 border-amber-200" : "bg-white border-slate-200"),
		children: [/* @__PURE__ */ (0, R.jsx)("p", {
			className: U("text-[11px] font-semibold", r ? "text-amber-700" : "text-slate-500"),
			children: e
		}), /* @__PURE__ */ (0, R.jsx)("p", {
			className: U("font-extrabold text-[14px]", r ? "text-amber-800" : "text-[#0f2a4a]"),
			children: mo(t) ? `— ${n ?? ""}`.trim() : G(t, n)
		})]
	});
}
function ac({ row: e }) {
	let t = [
		e.role ? `Vai trò: ${e.role}` : null,
		e.route ? `Tuyến: ${e.route}` : null,
		e.requiredDate ? `Khách cần giao: ${e.requiredDate}` : null,
		e.plannedDate ? `Kế hoạch: ${e.plannedDate}` : null,
		e.status ? `Trạng thái: ${e.status}` : null
	].filter(Boolean);
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-2xl bg-white border border-slate-200 p-4",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex items-center gap-2 flex-wrap",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "font-extrabold text-[16.5px] text-[#0f2a4a] break-all",
						children: e.shipmentId
					}),
					e.status ? /* @__PURE__ */ (0, R.jsx)(q, {
						tone: "blue",
						size: "sm",
						children: e.status
					}) : /* @__PURE__ */ (0, R.jsxs)(q, {
						tone: "gray",
						size: "sm",
						children: ["trạng thái ", "—"]
					}),
					e.financeCurrencies.map((e) => /* @__PURE__ */ (0, R.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
						children: e
					}, e)),
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "ml-auto shrink-0",
						children: e.canOpen ? /* @__PURE__ */ (0, R.jsx)(q, {
							tone: "green",
							size: "sm",
							children: "mở được"
						}) : /* @__PURE__ */ (0, R.jsx)(q, {
							tone: "amber",
							size: "sm",
							children: "không mở được"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "text-[13.5px] text-slate-600 mt-1.5 leading-relaxed",
				children: t.length ? t.join(" · ") : "Bối cảnh lô đang —"
			}),
			e.attention ? /* @__PURE__ */ (0, R.jsxs)("p", {
				className: "text-[13.5px] mt-1.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800",
				children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
					size: 15,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, R.jsxs)("span", { children: [e.attention, e.attentionDetail ? ` — ${e.attentionDetail}` : ""] })]
			}) : null,
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex flex-wrap items-center gap-2 mt-3",
				children: [e.canOpen ? /* @__PURE__ */ (0, R.jsxs)(L, {
					to: e.openHref,
					className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13.5px] px-4 min-h-[48px]",
					children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 16 }), " Mở lô"]
				}) : /* @__PURE__ */ (0, R.jsxs)("span", {
					className: "touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13.5px] px-4 min-h-[48px]",
					children: [/* @__PURE__ */ (0, R.jsx)(qi, { size: 15 }), " Lô không có trong dữ liệu hiện tại"]
				}), /* @__PURE__ */ (0, R.jsxs)("span", {
					className: "text-[12px] text-slate-400 break-words",
					children: ["nguồn: ", K(e.source)]
				})]
			})
		]
	});
}
function oc() {
	let e = (0, _.useSyncExternalStore)(C, S, S), t = e?.partnerContext ?? null, { toast: n } = Jn(), [r, i] = (0, _.useState)(""), [a, o] = (0, _.useState)(null), [s, c] = (0, _.useState)(!1), [l, u] = (0, _.useState)("create"), [d, f] = (0, _.useState)({ ...$s }), [p, m] = (0, _.useState)(null), [h, g] = (0, _.useState)(""), v = () => {
		u("create"), f({ ...$s }), g(""), c(!0);
	}, y = () => {
		let e = t?.identity?.party ?? null;
		e && (u("edit"), f({
			agentId: e.id ?? "",
			legalName: e.legalName ?? "",
			legalCode: e.legalCode ?? "",
			legalAddress: e.legalAddress ?? "",
			legalRepresentative: e.representative ?? "",
			representativeTitle: e.representativeTitle ?? "",
			phone: e.phone ?? "",
			email: e.email ?? "",
			bankAccountHolder: e.bankAccountHolder ?? "",
			bankAccountNumber: e.bankAccountNumber ?? "",
			bankName: e.bankName ?? "",
			bankBranch: e.bankBranch ?? ""
		}), g(""), c(!0));
	}, b = (e, t) => f((n) => ({
		...n,
		[e]: t
	})), x = () => {
		if (p) return;
		let e = d.agentId.trim().toUpperCase(), t = d.legalName.trim();
		if (!e) {
			g("Mã đại lý là bắt buộc.");
			return;
		}
		if (!t) {
			g("Tên pháp lý là bắt buộc — hồ sơ đại lý không tên không dùng được.");
			return;
		}
		let n = `agent-save-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
		if (!A("authority_agent_save", {
			agentId: e,
			requestId: n,
			legalName: t,
			legalCode: d.legalCode.trim(),
			legalAddress: d.legalAddress.trim(),
			legalRepresentative: d.legalRepresentative.trim(),
			representativeTitle: d.representativeTitle.trim(),
			phone: d.phone.trim(),
			email: d.email.trim(),
			bankAccountHolder: d.bankAccountHolder.trim(),
			bankAccountNumber: d.bankAccountNumber.trim(),
			bankName: d.bankName.trim(),
			bankBranch: d.bankBranch.trim()
		})) {
			g("Component chưa kết nối backend.");
			return;
		}
		g(""), m({
			requestId: n,
			agentId: e,
			mode: l
		});
	};
	(0, _.useEffect)(() => {
		if (!p || !e) return;
		let t = (e.lastWrites ?? []).find((e) => e.event === "authority_agent_save" && e.requestId === p.requestId);
		t && (t.ok ? (m(null), c(!1), n("Đã lưu hồ sơ đại lý " + p.agentId, "Ghi qua writer canonical authority_agents, có audit.", "green"), p.mode === "create" && (o(p.agentId), A("partner_context_select", { entityKey: p.agentId }))) : (m(null), g(t.error || "Backend từ chối lưu hồ sơ đại lý.")));
	}, [
		e,
		p,
		n
	]);
	let w = t?.options ?? [], T = t?.selectedKey ?? null, E = (0, _.useMemo)(() => {
		let e = r.trim().toLowerCase();
		return e ? w.filter((t) => [
			t.key,
			t.label,
			t.legalCode,
			t.phone,
			t.email
		].some((t) => (t ?? "").toLowerCase().includes(e))) : w;
	}, [w, r]), D = a !== null && a !== T, O = !!T && !D, k = (e) => {
		o(e), A("partner_context_select", { entityKey: e });
	}, ee = () => {
		o(null), A("partner_context_select", { entityKey: "" });
	}, j = t?.identity ?? null, M = j?.party ?? null, N = t?.finance ?? null, te = N?.rows ?? [], P = t?.shipments ?? [], F = t?.documents ?? [], ne = (0, _.useMemo)(() => new Set(P.filter((e) => e.canOpen).map((e) => e.shipmentId.toLowerCase())), [P]), re = t?.gaps ?? [], ie = t?.unavailable ?? [];
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Oi, {
							size: 20,
							className: "text-[#1e5aa8]"
						}),
						title: "Đại Lý Trường Thành",
						sub: "Quản lý hồ sơ đại lý của Trường Thành và xem các lô hàng, chứng từ, công nợ liên quan.",
						right: /* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: v,
							"aria-label": "Thêm đại lý",
							className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13.5px] px-4 min-h-[48px]",
							children: [/* @__PURE__ */ (0, R.jsx)(ha, { size: 16 }), " THÊM ĐẠI LÝ"]
						})
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [/* @__PURE__ */ (0, R.jsx)(Ta, {
							size: 19,
							className: "ml-3.5 text-slate-400 shrink-0"
						}), /* @__PURE__ */ (0, R.jsx)("input", {
							value: r,
							onChange: (e) => i(e.target.value),
							placeholder: "Tìm theo mã đối tác, tên, điện thoại hoặc email…",
							"aria-label": "Tìm đối tác",
							className: "w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[12.5px] text-slate-500 mt-1.5",
						children: [
							"Chỉ tìm trong ",
							(t?.searchFields ?? []).length,
							" trường hệ thống thật sự lưu:",
							(t?.searchFields ?? []).map((e) => ` ${e}`).join(" · ")
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-3",
						children: [w.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[14px] text-slate-500",
							children: [
								"Chưa có đối tác nào trong dữ liệu hiện tại — trạng thái là ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
								", không có danh sách mẫu."
							]
						}) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] font-bold uppercase tracking-wide text-slate-500 mb-2",
								children: [
									E.length,
									" / ",
									t?.optionCount ?? 0,
									" đối tác",
									t?.optionTruncated ? ` (giới hạn ${t.optionLimit})` : ""
								]
							}),
							/* @__PURE__ */ (0, R.jsx)("div", {
								className: "flex flex-wrap gap-2",
								children: E.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: () => k(e.key),
									"aria-pressed": e.key === T,
									className: U("btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 px-3.5 min-h-[48px] text-[14px] font-bold text-left", e.key === T ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"),
									children: [
										/* @__PURE__ */ (0, R.jsx)(Mr, {
											size: 16,
											className: "shrink-0"
										}),
										/* @__PURE__ */ (0, R.jsx)("span", {
											className: "break-words",
											children: e.label
										}),
										/* @__PURE__ */ (0, R.jsx)("span", {
											className: U("text-[11.5px] font-semibold", e.key === T ? "text-white/70" : "text-slate-400"),
											children: e.master ? "có master" : "chưa có master"
										})
									]
								}, e.key))
							}),
							E.length === 0 && /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[14px] text-slate-500 mt-2",
								children: [
									"Không có đối tác nào khớp “",
									r.trim(),
									"”. Hệ thống không tạo bản ghi mới để thay thế."
								]
							})
						] }), T && /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: ee,
							className: "btn-press touch-target mt-3 inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600",
							children: "Chọn đối tác khác"
						})]
					})
				]
			}),
			s && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-[#1e5aa8]/40 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: l === "create" ? /* @__PURE__ */ (0, R.jsx)(ha, { size: 18 }) : /* @__PURE__ */ (0, R.jsx)(la, { size: 18 }),
						title: l === "create" ? "Thêm đại lý mới" : `Sửa hồ sơ đại lý · ${d.agentId}`,
						sub: "Ghi vào master authority_agents hiện có qua writer canonical (quyền sales_write, có audit). Trường để trống được giữ là không xác định.",
						right: /* @__PURE__ */ (0, R.jsx)("span", {
							className: "rounded-lg bg-blue-50 px-2.5 py-1 text-[12px] font-bold text-blue-700",
							children: l === "create" ? "TẠO MỚI" : "CẬP NHẬT"
						})
					}),
					/* @__PURE__ */ (0, R.jsx)("div", {
						className: "grid grid-cols-1 md:grid-cols-2 gap-3 mt-3",
						children: ec.map((e) => {
							let t = l === "edit" && e.lockedOnEdit;
							return /* @__PURE__ */ (0, R.jsx)("div", {
								className: U(e.wide && "md:col-span-2"),
								children: /* @__PURE__ */ (0, R.jsx)(Y, {
									label: e.label,
									required: e.required,
									children: /* @__PURE__ */ (0, R.jsx)("input", {
										value: d[e.key],
										onChange: (t) => b(e.key, t.target.value),
										disabled: t || !!p,
										"aria-label": e.label,
										placeholder: t ? "" : "—",
										className: U(X(d[e.key].trim() ? "ok" : void 0), e.mono && "font-mono", t && "opacity-60 cursor-not-allowed")
									})
								})
							}, e.key);
						})
					}),
					h && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-4 rounded-xl border-2 border-red-200 bg-red-50 p-3.5 flex items-start gap-2.5",
						role: "alert",
						children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
							size: 18,
							className: "text-red-600 shrink-0 mt-0.5"
						}), /* @__PURE__ */ (0, R.jsxs)("div", { children: [/* @__PURE__ */ (0, R.jsx)("p", {
							className: "font-extrabold text-[14.5px] text-red-800",
							children: "Backend từ chối — hồ sơ chưa được lưu"
						}), /* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13.5px] text-red-700 mt-0.5 break-words",
							children: h
						})] })]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-col sm:flex-row gap-2.5 mt-4",
						children: [/* @__PURE__ */ (0, R.jsxs)("button", {
							onClick: x,
							disabled: !!p,
							"aria-label": "Lưu hồ sơ đại lý",
							className: "btn-press touch-target flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-60",
							children: [
								/* @__PURE__ */ (0, R.jsx)(xa, { size: 16 }),
								" ",
								p ? "ĐANG CHỜ BACKEND XÁC NHẬN…" : "LƯU HỒ SƠ ĐẠI LÝ"
							]
						}), /* @__PURE__ */ (0, R.jsx)("button", {
							onClick: () => {
								p || (c(!1), g(""));
							},
							disabled: !!p,
							className: "btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-60",
							children: "Hủy"
						})]
					})
				]
			}),
			D && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: "Đang đọc ngữ cảnh đối tác…"
				})
			}),
			!D && t && t.status === "NO_PARTNER_SOURCE" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-dashed border-amber-300 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(ja, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có nguồn dữ liệu đối tác"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed",
						children: t.reason
					})
				]
			}),
			!D && t && t.status === "PARTNER_NOT_FOUND" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-amber-300 p-6 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Ai, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Không tìm thấy đối tác"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1 leading-relaxed",
						children: t.reason
					})
				]
			}),
			!D && (!t || t.status === "NO_SELECTION") && w.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Oi, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Bảng ngữ cảnh đang trống"
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[14px] text-slate-500 mt-1",
						children: "Chọn một đối tác ở trên để xem hồ sơ pháp lý, lô liên kết và công nợ thật."
					})
				]
			}),
			O && t && /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex items-start gap-2 flex-wrap",
							children: [/* @__PURE__ */ (0, R.jsxs)("div", {
								className: "min-w-0",
								children: [
									/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[11.5px] font-extrabold uppercase tracking-wider text-[#1e5aa8]",
										children: "Hồ sơ pháp lý · danh tính"
									}),
									/* @__PURE__ */ (0, R.jsx)("h2", {
										className: "text-[19px] md:text-[21px] font-extrabold text-[#0f2a4a] break-words mt-0.5",
										children: K(j?.displayName)
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[13px] text-slate-500 mt-0.5 break-all",
										children: [
											"Mã: ",
											K(j?.displayId),
											" · ",
											(t.matchedSources ?? []).join(" · ") || "—"
										]
									})
								]
							}), /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "ml-auto shrink-0 flex items-center gap-1.5",
								children: [/* @__PURE__ */ (0, R.jsxs)(q, {
									tone: nc(j?.masterStatus),
									size: "sm",
									children: ["master: ", j?.masterStatus === "KNOWN" ? "CÓ HỒ SƠ" : "CHƯA CÓ"]
								}), M && /* @__PURE__ */ (0, R.jsxs)("button", {
									onClick: y,
									"aria-label": "Sửa hồ sơ đại lý",
									className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8]/50 text-[#1e5aa8] font-bold text-[13px] px-3.5 min-h-[44px]",
									children: [/* @__PURE__ */ (0, R.jsx)(la, { size: 15 }), " Sửa hồ sơ đại lý"]
								})]
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[12.5px] text-slate-400 mt-2 break-words",
							children: [
								"Nguồn danh tính: ",
								K(j?.masterSource),
								j?.contextName ? ` · ngữ cảnh lô ghi nhận: ${j.contextName}${j.contextId ? ` (${j.contextId})` : ""}` : ""
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)(rc, {
									label: "Mã số thuế / pháp lý",
									value: M?.legalCode,
									mono: !0
								}),
								/* @__PURE__ */ (0, R.jsx)(rc, {
									label: "Điện thoại",
									value: M?.phone,
									mono: !0
								}),
								/* @__PURE__ */ (0, R.jsx)(rc, {
									label: "Email",
									value: M?.email
								}),
								/* @__PURE__ */ (0, R.jsx)(rc, {
									label: "Người đại diện",
									value: M ? `${M.representative}${M.representativeTitle ? ` — ${M.representativeTitle}` : ""}` : null
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "rounded-xl bg-slate-50 border border-slate-200 p-3 sm:col-span-2 lg:col-span-2",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
										children: "Địa chỉ pháp lý"
									}), /* @__PURE__ */ (0, R.jsx)("p", {
										className: "mt-0.5 font-semibold text-[14.5px] break-words",
										children: K(M?.legalAddress)
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "mt-3 rounded-xl border-2 border-slate-100 bg-slate-50/60 p-3",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-slate-500",
								children: "Tài khoản thanh toán (nguyên văn từ master)"
							}), /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "grid gap-2 mt-2 sm:grid-cols-2 lg:grid-cols-4",
								children: [
									/* @__PURE__ */ (0, R.jsx)(rc, {
										label: "Chủ tài khoản",
										value: M?.bankAccountHolder
									}),
									/* @__PURE__ */ (0, R.jsx)(rc, {
										label: "Số tài khoản",
										value: M?.bankAccountNumber,
										mono: !0
									}),
									/* @__PURE__ */ (0, R.jsx)(rc, {
										label: "Ngân hàng",
										value: M?.bankName
									}),
									/* @__PURE__ */ (0, R.jsx)(rc, {
										label: "Chi nhánh",
										value: M?.bankBranch
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2 mt-3",
							children: [/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "text-[12.5px] font-bold text-slate-500 inline-flex items-center gap-1.5",
								children: [/* @__PURE__ */ (0, R.jsx)(da, { size: 14 }), " Vai trò theo lô:"]
							}), (t.roles ?? []).length === 0 ? /* @__PURE__ */ (0, R.jsx)("span", {
								className: "text-[13.5px] font-semibold text-slate-400",
								children: "—"
							}) : (t.roles ?? []).map((e) => /* @__PURE__ */ (0, R.jsx)("span", {
								className: "rounded-full bg-slate-100 px-3 py-1 text-[12.5px] font-bold text-slate-600",
								children: e
							}, e))]
						})
					]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(gr, { size: 18 }),
						title: `Lô hàng liên kết · ${t.shipmentCount ?? 0}`,
						sub: "Mã lô lấy từ chính dữ liệu; chi tiết lô không bị lặp lại ở đây — bấm Mở lô để sang màn hình Lô hàng."
					}), P.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-2",
						children: [
							"Chưa có lô nào liên kết với đối tác này trong dữ liệu hiện tại — ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
							", không phải 0 lô."
						]
					}) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "hidden lg:block mt-3 overflow-x-auto",
							children: /* @__PURE__ */ (0, R.jsxs)("table", {
								className: "tbl w-full text-[14px] min-w-[900px]",
								children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Lô" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Vai trò" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Tuyến" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Khách cần giao" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Kế hoạch" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Trạng thái" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Chú ý" }),
									/* @__PURE__ */ (0, R.jsx)("th", { children: "Hành động" })
								] }) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: P.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
									className: "hover:bg-slate-50",
									children: [
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "font-extrabold text-[#1e5aa8] whitespace-nowrap",
											children: e.shipmentId
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: K(e.role) }),
										/* @__PURE__ */ (0, R.jsx)("td", { children: K(e.route) }),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "whitespace-nowrap",
											children: K(e.requiredDate)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "whitespace-nowrap",
											children: K(e.plannedDate)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: K(e.status) }),
										/* @__PURE__ */ (0, R.jsx)("td", {
											className: "max-w-[220px] text-[13px]",
											children: K(e.attention)
										}),
										/* @__PURE__ */ (0, R.jsx)("td", { children: e.canOpen ? /* @__PURE__ */ (0, R.jsxs)(L, {
											to: e.openHref,
											className: "btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]",
											children: [/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }), " Mở lô"]
										}) : /* @__PURE__ */ (0, R.jsxs)("span", {
											className: "inline-flex items-center gap-1 text-[12.5px] font-bold text-slate-400",
											children: [/* @__PURE__ */ (0, R.jsx)(qi, { size: 13 }), " không mở được"]
										}) })
									]
								}, e.shipmentId)) })]
							})
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "lg:hidden space-y-3 mt-3",
							children: P.map((e) => /* @__PURE__ */ (0, R.jsx)(ac, { row: e }, e.shipmentId))
						}),
						t.shipmentTruncated && /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[12.5px] text-amber-700 font-semibold mt-2",
							children: [
								"Danh sách rút gọn — còn ",
								Math.max(0, (t.shipmentCount ?? 0) - P.length),
								" lô khác chưa hiển thị."
							]
						})
					] })]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [
						/* @__PURE__ */ (0, R.jsx)(J, {
							icon: /* @__PURE__ */ (0, R.jsx)(ro, {
								size: 18,
								className: "text-[#1e5aa8]"
							}),
							title: "Công nợ phải trả theo lô",
							sub: N?.note ?? "",
							right: /* @__PURE__ */ (0, R.jsx)(q, {
								tone: nc(N?.status),
								size: "sm",
								children: K(N?.statusLabel)
							})
						}),
						te.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "text-[14px] text-slate-500 mt-2",
							children: [
								"Chưa có nghĩa vụ/thanh toán canonical nào cho đối tác này. Phải trả: ",
								/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
								" — hệ thống không hiển thị 0."
							]
						}) : /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "space-y-2.5 mt-3",
							children: [te.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
								className: "rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3",
								children: [
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "flex items-center gap-2 flex-wrap",
										children: [
											e.shipmentId && ne.has(e.shipmentId.toLowerCase()) ? /* @__PURE__ */ (0, R.jsx)(L, {
												to: `/lo-hang/${e.shipmentId}?tab=tai-chinh`,
												className: "font-extrabold text-[15.5px] text-[#1e5aa8] hover:underline break-all",
												children: e.shipmentId
											}) : /* @__PURE__ */ (0, R.jsx)("span", {
												className: "font-extrabold text-[15.5px] text-[#0f2a4a] break-all",
												children: K(e.shipmentId)
											}),
											/* @__PURE__ */ (0, R.jsx)("span", {
												className: "rounded-md bg-white border px-2 py-0.5 text-[12px] font-bold",
												children: K(e.currency)
											}),
											/* @__PURE__ */ (0, R.jsx)(q, {
												tone: nc(e.status),
												size: "sm",
												children: K(e.status)
											}),
											/* @__PURE__ */ (0, R.jsxs)("span", {
												className: "ml-auto text-[11.5px] text-slate-400",
												children: [e.obligationIds.length, " nghĩa vụ"]
											})
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("div", {
										className: "grid grid-cols-3 gap-2 mt-2",
										children: [
											/* @__PURE__ */ (0, R.jsx)(ic, {
												label: "Phải trả",
												value: e.payable,
												ccy: e.currency
											}),
											/* @__PURE__ */ (0, R.jsx)(ic, {
												label: "Đã trả",
												value: e.paid,
												ccy: e.currency
											}),
											/* @__PURE__ */ (0, R.jsx)(ic, {
												label: "Còn lại",
												value: e.remaining,
												ccy: e.currency,
												strong: !0
											})
										]
									}),
									/* @__PURE__ */ (0, R.jsxs)("p", {
										className: "text-[11.5px] text-slate-400 mt-1.5 break-words",
										children: ["nguồn: ", K(e.source)]
									})
								]
							}, e.id ?? `${e.shipmentId}-${e.currency}-${t}`)), /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12.5px] text-slate-500",
								children: [Object.entries(N?.byCurrency ?? {}).map(([e, t]) => `${e}: ${t.rowCount} dòng · ${t.shipmentIds.length} lô`).join(" · ") || "—", " — không cộng gộp khác loại tiền tệ, không tổng hợp công nợ toàn đối tác tại đây."]
							})]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "flex flex-wrap gap-2.5 mt-3",
							children: [/* @__PURE__ */ (0, R.jsxs)(L, {
								to: N?.worklistHref ?? "/tai-chinh/cong-no-doi-tac",
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[48px]",
								children: ["Mở Công nợ đối tác ", /* @__PURE__ */ (0, R.jsx)(gr, { size: 16 })]
							}), /* @__PURE__ */ (0, R.jsx)(L, {
								to: "/lo-hang",
								className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[48px]",
								children: "Xem Lô Hàng"
							})]
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[12.5px] text-slate-400 mt-2",
							children: "Số liệu do sổ cái canonical dẫn xuất (C2B/C2D); màn hình này chỉ đọc lại, không tự tính."
						})
					]
				}),
				F.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
					children: [/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Ai, { size: 18 }),
						title: `Tài liệu bằng chứng theo lô · ${F.length}`,
						sub: "Dự phóng từ hồ sơ lô hiện có — không có kho tài liệu riêng của đối tác."
					}), /* @__PURE__ */ (0, R.jsx)("div", {
						className: "grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3",
						children: F.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-xl bg-slate-50 border border-slate-200 p-3",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a] break-all",
									children: K(e.document)
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] text-slate-500 mt-0.5 break-all",
									children: [
										K(e.shipmentId),
										" · ",
										K(e.status)
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[11.5px] text-slate-400 mt-1 break-words",
									children: ["nguồn: ", K(e.source)]
								})
							]
						}, `${e.shipmentId}-${e.document}-${t}`))
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid gap-3 lg:grid-cols-2",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-amber-700",
								children: "Context còn thiếu / chưa xác định"
							}),
							/* @__PURE__ */ (0, R.jsxs)("ul", {
								className: "mt-2 space-y-1.5",
								children: [re.map((e) => /* @__PURE__ */ (0, R.jsxs)("li", {
									className: "text-[13.5px] text-slate-600 flex items-start gap-2",
									children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
										size: 15,
										className: "shrink-0 mt-0.5 text-amber-600"
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "break-words",
										children: e
									})]
								}, e)), re.length === 0 && /* @__PURE__ */ (0, R.jsx)("li", {
									className: "text-[13.5px] text-slate-500",
									children: "Không có missing field nào trong dữ liệu hiện có."
								})]
							}),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[12px] text-slate-400 mt-2.5",
								children: [
									"Trường thiếu hiển thị “",
									"—",
									"” — hệ thống không điền 0 và không suy đoán."
								]
							})
						]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
						children: [
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[11.5px] font-extrabold uppercase tracking-wider text-slate-500",
								children: "Context không khả dụng trong hệ thống"
							}),
							/* @__PURE__ */ (0, R.jsx)("ul", {
								className: "mt-2 space-y-1.5",
								children: ie.map((e) => /* @__PURE__ */ (0, R.jsxs)("li", {
									className: "text-[13.5px] text-slate-600 flex items-start gap-2",
									children: [/* @__PURE__ */ (0, R.jsx)(qi, {
										size: 14,
										className: "shrink-0 mt-1 text-slate-400"
									}), /* @__PURE__ */ (0, R.jsx)("span", {
										className: "break-words",
										children: e
									})]
								}, e))
							}),
							/* @__PURE__ */ (0, R.jsx)("p", {
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
var sc = {
	obligation: "Phải trả / nghĩa vụ",
	money: "Tiền đã phát sinh"
}, cc = {
	MATCHED: "green",
	ALLOCATED: "green",
	PARTIAL: "amber",
	UNMATCHED: "red",
	UNALLOCATED: "red"
};
function lc(e) {
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
var uc = [
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
function dc(e) {
	return [
		`q=${(e.query ?? "").trim().toLowerCase()}`,
		`c=${(e.currency ?? "ALL").trim().toUpperCase()}`,
		`s=${(e.state ?? "ALL").trim().toUpperCase()}`,
		`d=${(e.side ?? "ALL").trim().toUpperCase()}`
	].join("|");
}
function fc({ value: e, ccy: t, strong: n }) {
	return /* @__PURE__ */ (0, R.jsx)("span", {
		className: U("tabular-nums whitespace-nowrap", n ? "font-extrabold text-[#0f2a4a]" : "font-bold"),
		children: mo(e) ? `— ${t}`.trim() : G(e, t)
	});
}
function pc({ row: e }) {
	return e.matchState ? /* @__PURE__ */ (0, R.jsx)(q, {
		tone: cc[e.matchState] ?? "gray",
		size: "sm",
		children: e.matchLabel ?? e.matchState
	}) : /* @__PURE__ */ (0, R.jsxs)(q, {
		tone: "gray",
		size: "sm",
		children: ["trạng thái ", "—"]
	});
}
function mc({ row: e }) {
	let t = [
		e.obligationIds.length ? `nghĩa vụ: ${e.obligationIds.join(", ")}` : null,
		e.transactionIds.length ? `giao dịch: ${e.transactionIds.join(", ")}` : null,
		e.allocationIds.length ? `phân bổ: ${e.allocationIds.join(", ")}` : null
	].filter(Boolean);
	return /* @__PURE__ */ (0, R.jsx)("p", {
		className: "text-[12px] text-slate-500 break-words leading-relaxed",
		children: t.length ? t.join(" · ") : "Chưa có tham chiếu phân bổ — —"
	});
}
function hc({ row: e }) {
	return e.canOpen ? /* @__PURE__ */ (0, R.jsxs)(L, {
		to: e.openHref,
		className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13px] px-3.5 min-h-[44px]",
		children: [
			/* @__PURE__ */ (0, R.jsx)(mi, { size: 15 }),
			" Mở lô ",
			e.shipmentId
		]
	}) : /* @__PURE__ */ (0, R.jsxs)("span", {
		className: "touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13px] px-3.5 min-h-[44px]",
		children: [/* @__PURE__ */ (0, R.jsx)(qi, { size: 14 }), " Lô không có trong dữ liệu"]
	});
}
function gc({ row: e }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "rounded-2xl bg-white border border-slate-200 p-4",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex items-center gap-2 flex-wrap",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "font-extrabold text-[16px] text-[#0f2a4a] break-all",
						children: e.shipmentId
					}),
					/* @__PURE__ */ (0, R.jsx)(pc, { row: e }),
					/* @__PURE__ */ (0, R.jsx)(q, {
						tone: e.side === "obligation" ? "blue" : "gray",
						size: "sm",
						children: sc[e.side] ?? e.side
					}),
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold",
						children: e.currency
					}),
					e.reviewReason ? /* @__PURE__ */ (0, R.jsx)(q, {
						tone: "amber",
						size: "sm",
						children: "cần rà soát"
					}) : null
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "text-[13.5px] text-slate-600 mt-1.5 break-words",
				children: [K(e.partnerName), e.purpose ? ` · ${K(e.purpose)}` : ""]
			}),
			e.occurredAt ? /* @__PURE__ */ (0, R.jsxs)("p", {
				className: "text-[12.5px] text-slate-500 mt-0.5",
				children: ["Phát sinh: ", e.occurredAt]
			}) : null,
			/* @__PURE__ */ (0, R.jsx)("div", {
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
				].map((t) => /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-xl bg-slate-50 border border-slate-200 p-2 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
						children: t.label
					}), /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[13px] mt-0.5",
						children: /* @__PURE__ */ (0, R.jsx)(fc, {
							value: t.value,
							ccy: e.currency
						})
					})]
				}, t.label))
			}),
			e.reviewReason ? /* @__PURE__ */ (0, R.jsxs)("p", {
				className: "text-[13px] mt-2.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800",
				children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
					size: 15,
					className: "shrink-0 mt-0.5"
				}), /* @__PURE__ */ (0, R.jsx)("span", { children: e.reviewReason })]
			}) : null,
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "mt-3",
				children: /* @__PURE__ */ (0, R.jsx)(mc, { row: e })
			}),
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "mt-3",
				children: /* @__PURE__ */ (0, R.jsx)(hc, { row: e })
			})
		]
	});
}
function _c({ options: e, value: t, onPick: n, ariaLabel: r }) {
	return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "flex flex-wrap gap-2",
		role: "group",
		"aria-label": r,
		children: e.map((e) => /* @__PURE__ */ (0, R.jsx)("button", {
			onClick: () => n(e.value),
			"aria-pressed": e.value === t,
			className: U("btn-press touch-target rounded-xl border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold", e.value === t ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a]"),
			children: e.label
		}, e.value))
	});
}
function vc() {
	(0, _.useSyncExternalStore)(C, S, S);
	let e = S()?.reconciliation ?? null, [t, n] = (0, _.useState)(""), [r, i] = (0, _.useState)(null), a = e?.rows ?? [], o = e?.totals ?? {}, s = e?.currencies ?? [], c = e?.side ?? "ALL", l = e?.state ?? "ALL", u = e?.currency ?? "ALL", d = (0, _.useMemo)(() => a.filter((e) => e.reviewReason), [a]), f = (e) => {
		let n = {
			query: e.query ?? t,
			currency: e.currency ?? u,
			state: e.state ?? l,
			side: e.side ?? c
		};
		e.side && e.side !== c && !e.state && (n.state = "ALL"), i(dc(n)), A("reconciliation_filter", n);
	}, p = () => {
		n("");
		let e = {
			query: "",
			currency: "ALL",
			state: "ALL",
			side: "ALL"
		};
		i(dc(e)), A("reconciliation_filter", e);
	}, m = e ? dc({
		query: e.query,
		currency: e.currency,
		state: e.state,
		side: e.side
	}) : null, h = r !== null && m !== null && r !== m, g = !(!e || !e.query && e.currency === "ALL" && e.state === "ALL" && e.side === "ALL");
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "space-y-4 max-w-[1300px]",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Ca, {
							size: 20,
							className: "text-white"
						}),
						title: "Đối soát",
						sub: "Nghĩa vụ đã được phân bổ tới đâu, và khoản tiền nào chưa được phân bổ — đọc từ ledger canonical. Màn hình chỉ đọc, không ghi, không sửa số dư.",
						right: /* @__PURE__ */ (0, R.jsxs)("span", {
							className: "hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-[12px] font-bold text-slate-600",
							children: [/* @__PURE__ */ (0, R.jsx)(qi, { size: 13 }), " CHỈ ĐỌC"]
						})
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden",
						children: [
							/* @__PURE__ */ (0, R.jsx)(Ta, {
								size: 19,
								className: "ml-3.5 text-slate-400 shrink-0"
							}),
							/* @__PURE__ */ (0, R.jsx)("input", {
								value: t,
								onChange: (e) => n(e.target.value),
								onKeyDown: (e) => {
									e.key === "Enter" && f({ query: t });
								},
								placeholder: "Tìm theo mã lô, mã nghĩa vụ, mã giao dịch, phân bổ hoặc tên đối tác…",
								"aria-label": "Tìm trong đối soát",
								className: "w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
							}),
							/* @__PURE__ */ (0, R.jsx)("button", {
								onClick: () => f({ query: t }),
								className: "btn-press touch-target shrink-0 mr-2 rounded-lg bg-[#1e5aa8] text-white font-bold text-[13.5px] px-3.5 min-h-[40px]",
								children: "Tìm"
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-3 space-y-2.5",
						children: [
							/* @__PURE__ */ (0, R.jsx)(_c, {
								ariaLabel: "Lọc theo loại dòng",
								options: uc,
								value: c,
								onPick: (e) => f({ side: e })
							}),
							/* @__PURE__ */ (0, R.jsx)(_c, {
								ariaLabel: "Lọc theo trạng thái đối soát",
								options: lc(c),
								value: lc(c).some((e) => e.value === l) ? l : "ALL",
								onPick: (e) => f({ state: e })
							}),
							/* @__PURE__ */ (0, R.jsx)(_c, {
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
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap items-center gap-x-3 gap-y-1 mt-3",
						children: [
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "text-[13px] text-slate-500",
								children: [
									"Hiển thị ",
									/* @__PURE__ */ (0, R.jsx)("b", { children: e?.visibleCount ?? 0 }),
									" / ",
									e?.totalCount ?? 0,
									" dòng",
									e?.truncated ? ` (giới hạn ${e?.maxRows})` : ""
								]
							}),
							g ? /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12.5px] text-slate-400",
								children: "Bộ lọc chỉ thu hẹp danh sách — tổng theo tiền tệ ở dưới vẫn là toàn bộ ledger."
							}) : null,
							g ? /* @__PURE__ */ (0, R.jsxs)("button", {
								onClick: p,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600",
								children: [/* @__PURE__ */ (0, R.jsx)(Sr, { size: 15 }), " Bỏ lọc"]
							}) : null
						]
					})
				]
			}),
			h && /* @__PURE__ */ (0, R.jsx)("div", {
				className: "rounded-2xl bg-white border border-slate-200 p-8 text-center",
				children: /* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[15px] font-semibold text-slate-500",
					children: "Đang đọc ledger canonical…"
				})
			}),
			e && e.status === "NO_SOURCE" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl bg-white border-2 border-dashed border-red-300 p-8 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-red-50 text-red-600 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Wr, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa đọc được ledger canonical"
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed",
						children: [
							e.error ?? "Không có kết nối tới cơ sở dữ liệu.",
							" Hệ thống không tự tạo số liệu thay thế: trạng thái là ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
							", không phải 0."
						]
					})
				]
			}),
			e && e.status === "EMPTY" && /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center",
						children: /* @__PURE__ */ (0, R.jsx)(Ca, { size: 26 })
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "text-[16px] font-extrabold text-[#0f2a4a] mt-3",
						children: "Chưa có bản ghi đối soát"
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "text-[14px] text-slate-500 mt-1 max-w-[620px] mx-auto leading-relaxed",
						children: [
							"Chưa có nghĩa vụ hay giao dịch canonical nào gắn với lô hàng. Đây là trạng thái",
							/* @__PURE__ */ (0, R.jsx)("b", { children: " chưa có dữ liệu" }),
							", không phải công nợ bằng 0."
						]
					})
				]
			}),
			e && e.status !== "EMPTY" && e.status !== "NO_SOURCE" && /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [
				s.length > 0 && /* @__PURE__ */ (0, R.jsx)("div", {
					className: "grid gap-3 md:grid-cols-2",
					children: s.map((e) => {
						let t = o[e];
						if (!t) return null;
						let n = t.states ?? {};
						return /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl bg-white border border-slate-200 p-4",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "flex items-center gap-2 flex-wrap",
									children: [
										/* @__PURE__ */ (0, R.jsx)("h3", {
											className: "text-[16px] font-extrabold text-[#0f2a4a]",
											children: e
										}),
										e === "UNKNOWN" ? /* @__PURE__ */ (0, R.jsx)(q, {
											tone: "gray",
											size: "sm",
											children: "chưa rõ tiền tệ"
										}) : null,
										t.review.count > 0 ? /* @__PURE__ */ (0, R.jsxs)(q, {
											tone: "amber",
											size: "sm",
											children: [t.review.count, " dòng cần rà soát"]
										}) : null
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12px] text-slate-400 mt-0.5",
									children: [
										t.obligations.count,
										" nghĩa vụ · ",
										t.money.count,
										" giao dịch"
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "grid grid-cols-3 gap-2 mt-3",
									children: [
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
												children: "Phải trả"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, R.jsx)(fc, {
													value: t.obligations.amount,
													ccy: e
												})
											})]
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-slate-500",
												children: "Đã phân bổ"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, R.jsx)(fc, {
													value: t.obligations.allocated,
													ccy: e
												})
											})]
										}),
										/* @__PURE__ */ (0, R.jsxs)("div", {
											className: "rounded-xl bg-amber-50 border border-amber-200 p-2.5 text-center",
											children: [/* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[10.5px] font-bold uppercase tracking-wide text-amber-700",
												children: "Còn lại"
											}), /* @__PURE__ */ (0, R.jsx)("p", {
												className: "text-[13.5px] mt-0.5",
												children: /* @__PURE__ */ (0, R.jsx)(fc, {
													value: t.obligations.remaining,
													ccy: e,
													strong: !0
												})
											})]
										})
									]
								}),
								/* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] text-slate-500 mt-2.5",
									children: ["Tiền chưa phân bổ: ", /* @__PURE__ */ (0, R.jsx)(fc, {
										value: t.money.unallocated,
										ccy: e
									})]
								}),
								/* @__PURE__ */ (0, R.jsx)("div", {
									className: "flex flex-wrap gap-1.5 mt-2.5",
									children: Object.entries(n).filter(([, e]) => e > 0).map(([e, t]) => /* @__PURE__ */ (0, R.jsxs)("span", {
										className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600",
										children: [
											e,
											": ",
											t
										]
									}, e))
								}),
								t.review.count > 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
									className: "text-[12.5px] mt-2 text-amber-800",
									children: ["Trong đó cần rà soát: ", /* @__PURE__ */ (0, R.jsx)(fc, {
										value: t.review.amount,
										ccy: e
									})]
								}) : null
							]
						}, e);
					})
				}),
				d.length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-amber-50 border-2 border-amber-200 p-4",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "inline-flex items-center gap-1.5 text-[14px] font-extrabold text-amber-900",
							children: [
								/* @__PURE__ */ (0, R.jsx)(Wr, { size: 16 }),
								" ",
								d.length,
								" dòng cần rà soát"
							]
						}),
						/* @__PURE__ */ (0, R.jsx)("ul", {
							className: "mt-2 space-y-1",
							children: d.slice(0, 8).map((e) => /* @__PURE__ */ (0, R.jsxs)("li", {
								className: "text-[13px] text-amber-900 break-words",
								children: [
									/* @__PURE__ */ (0, R.jsx)("b", { children: e.shipmentId }),
									" · ",
									K(e.partnerName),
									" · ",
									e.currency,
									" — ",
									e.reviewReason
								]
							}, e.id))
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[12.5px] text-amber-800 mt-2",
							children: "Dòng cần rà soát vẫn được cộng trong tổng của tiền tệ đó và được nêu riêng ở đây — không bị ẩn, cũng không tự động coi là đã đối soát."
						})
					]
				}),
				a.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl border-2 border-dashed border-slate-300 bg-white p-8 text-center",
					children: [/* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[15px] font-extrabold text-[#0f2a4a]",
						children: "Không có dòng nào khớp bộ lọc"
					}), /* @__PURE__ */ (0, R.jsx)("p", {
						className: "text-[13.5px] text-slate-500 mt-1",
						children: "Tổng theo tiền tệ ở trên vẫn là toàn bộ ledger — bộ lọc không làm thay đổi số tổng."
					})]
				}) : /* @__PURE__ */ (0, R.jsxs)(R.Fragment, { children: [/* @__PURE__ */ (0, R.jsx)("div", {
					className: "space-y-3 md:hidden",
					children: a.map((e) => /* @__PURE__ */ (0, R.jsx)(gc, { row: e }, e.id))
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden",
					children: /* @__PURE__ */ (0, R.jsxs)("table", {
						className: "w-full text-[13.5px]",
						children: [/* @__PURE__ */ (0, R.jsx)("thead", {
							className: "bg-slate-50 text-slate-500",
							children: /* @__PURE__ */ (0, R.jsx)("tr", { children: [
								"Lô hàng",
								"Đối tác",
								"Loại",
								"Trạng thái",
								"Số tiền",
								"Đã phân bổ",
								"Còn lại",
								"Tiền tệ",
								"Thao tác"
							].map((e) => /* @__PURE__ */ (0, R.jsx)("th", {
								className: "text-left font-bold text-[11.5px] uppercase tracking-wide px-3 py-2.5",
								children: e
							}, e)) })
						}), /* @__PURE__ */ (0, R.jsx)("tbody", { children: a.map((e) => /* @__PURE__ */ (0, R.jsxs)("tr", {
							className: "border-t border-slate-100 align-top",
							children: [
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "px-3 py-2.5",
									children: [/* @__PURE__ */ (0, R.jsx)("p", {
										className: "font-extrabold text-[#0f2a4a] break-all",
										children: e.shipmentId
									}), /* @__PURE__ */ (0, R.jsx)(mc, { row: e })]
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "px-3 py-2.5 break-words",
									children: [
										/* @__PURE__ */ (0, R.jsx)("p", {
											className: "font-semibold",
											children: K(e.partnerName)
										}),
										e.purpose ? /* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-slate-500",
											children: e.purpose
										}) : null,
										e.occurredAt ? /* @__PURE__ */ (0, R.jsx)("p", {
											className: "text-[12px] text-slate-500",
											children: e.occurredAt
										}) : null
									]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5 whitespace-nowrap",
									children: sc[e.side] ?? e.side
								}),
								/* @__PURE__ */ (0, R.jsxs)("td", {
									className: "px-3 py-2.5",
									children: [/* @__PURE__ */ (0, R.jsx)(pc, { row: e }), e.reviewReason ? /* @__PURE__ */ (0, R.jsx)("p", {
										className: "text-[12px] text-amber-800 mt-1 break-words",
										children: e.reviewReason
									}) : null]
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, R.jsx)(fc, {
										value: e.amount,
										ccy: e.currency
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, R.jsx)(fc, {
										value: e.allocated,
										ccy: e.currency
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, R.jsx)(fc, {
										value: e.remaining,
										ccy: e.currency,
										strong: !0
									})
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5 whitespace-nowrap font-bold",
									children: e.currency
								}),
								/* @__PURE__ */ (0, R.jsx)("td", {
									className: "px-3 py-2.5",
									children: /* @__PURE__ */ (0, R.jsx)(hc, { row: e })
								})
							]
						}, e.id)) })]
					})
				})] }),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-white border border-slate-200 p-4",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, R.jsx)(ro, { size: 15 }), " Ghi nhận ở đâu"]
						}),
						/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[13px] text-slate-500 mt-1",
							children: "Bàn đối soát không ghi. Ghi nhận phải trả, thanh toán đối tác và thu tiền khách vẫn đi qua writer canonical có RBAC, audit và idempotency riêng."
						}),
						/* @__PURE__ */ (0, R.jsx)("div", {
							className: "flex flex-wrap gap-2 mt-3",
							children: (e.actions ?? []).map((e) => /* @__PURE__ */ (0, R.jsxs)(L, {
								to: e.href,
								className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8] text-[#1e5aa8] font-bold text-[13.5px] px-3.5 min-h-[44px]",
								children: [
									/* @__PURE__ */ (0, R.jsx)(vr, { size: 15 }),
									" ",
									e.label
								]
							}, e.href))
						})
					]
				}),
				(e.unavailable ?? []).length > 0 && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl bg-slate-50 border border-slate-200 p-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [/* @__PURE__ */ (0, R.jsx)(Ai, { size: 15 }), " Ngoài phạm vi bàn này"]
					}), /* @__PURE__ */ (0, R.jsx)("ul", {
						className: "mt-2 space-y-1",
						children: (e.unavailable ?? []).map((e) => /* @__PURE__ */ (0, R.jsxs)("li", {
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
var yc = {
	Khan: "Khẩn",
	CanXuLy: "Cần xử lý"
};
function bc({ position: e, kind: t }) {
	let n = t === "receivable", r = n ? "phải thu" : "phải trả", i = n ? "text-red-700" : "text-amber-800", a = n ? "bg-red-50 border-red-200" : "bg-amber-50 border-amber-200", o = e.incompleteRowCount > 0 ? "dòng còn mở đã xác định" : "dòng còn mở", s = n ? "dòng chưa đủ Finance Actual, không tính là 0" : "dòng chưa đủ số dư canonical, không tính là 0";
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		"data-testid": `ceo-${t}-${e.currency}`,
		"data-ceo-currency": e.currency,
		className: `min-w-0 rounded-2xl border p-3.5 md:p-4 ${a}`,
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex items-center justify-between gap-2",
				children: [/* @__PURE__ */ (0, R.jsx)("span", {
					className: "rounded-md bg-white/80 border border-slate-200 px-2 py-0.5 text-[12px] font-extrabold tracking-wide text-[#0f2a4a]",
					children: e.currency
				}), /* @__PURE__ */ (0, R.jsxs)("span", {
					className: "text-right text-[12px] leading-snug font-semibold text-slate-500",
					children: [
						bo(e.openCount),
						" ",
						o
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-3 text-[12.5px] font-bold uppercase tracking-wide text-slate-600",
				children: ["Còn ", r]
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: `mt-1 break-words text-[20px] leading-tight font-extrabold md:text-[23px] ${i}`,
				children: G(e.outstanding, e.currency)
			}),
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-2 text-[12.5px] leading-relaxed text-slate-500",
				children: [bo(e.rowCount), " dòng nguồn đủ điều kiện · không quy đổi sang tiền tệ khác"]
			}),
			e.incompleteRowCount > 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-1 text-[12.5px] leading-relaxed font-semibold text-amber-800",
				children: [
					bo(e.incompleteRowCount),
					" ",
					s,
					"."
				]
			}) : null
		]
	});
}
function xc({ label: e, value: t, tone: n = "gray" }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: `min-w-0 rounded-xl border px-3 py-2.5 ${{
			green: "border-emerald-200 bg-emerald-50 text-emerald-800",
			amber: "border-amber-200 bg-amber-50 text-amber-900",
			red: "border-red-200 bg-red-50 text-red-800",
			gray: "border-slate-200 bg-slate-50 text-slate-700"
		}[n]}`,
		children: [/* @__PURE__ */ (0, R.jsx)("p", {
			className: "text-[11.5px] font-bold uppercase tracking-wide opacity-75",
			children: e
		}), /* @__PURE__ */ (0, R.jsx)("p", {
			className: "mt-0.5 text-[18px] leading-tight font-extrabold",
			children: bo(t)
		})]
	});
}
function Sc({ children: e }) {
	return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
		children: e
	});
}
function Cc({ counts: e, total: t }) {
	let n = [...e].sort((e, t) => t.count - e.count || e.status.localeCompare(t.status, "vi")), r = [
		"bg-[#1e5aa8]",
		"bg-sky-500",
		"bg-emerald-500",
		"bg-amber-500",
		"bg-violet-500",
		"bg-rose-400"
	];
	return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "space-y-2.5",
		"data-testid": "ceo-status-visual",
		children: n.map((e, n) => {
			let i = e.share ?? 0, a = i > 0 ? Math.max(i * 100, 2.5) : 0;
			return /* @__PURE__ */ (0, R.jsxs)("div", {
				"data-testid": "ceo-status-row",
				className: "min-w-0",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "flex items-baseline justify-between gap-2",
					children: [/* @__PURE__ */ (0, R.jsx)("span", {
						className: "min-w-0 truncate text-[13.5px] font-semibold text-slate-700",
						children: e.status
					}), /* @__PURE__ */ (0, R.jsxs)("span", {
						className: "shrink-0 text-[13.5px] font-extrabold text-[#0f2a4a]",
						children: [bo(e.count), /* @__PURE__ */ (0, R.jsxs)("span", {
							className: "ml-1 font-semibold text-slate-400",
							children: [
								"· ",
								i > 0 ? Math.round(i * 100) : 0,
								"% / ",
								bo(t),
								" lô"
							]
						})]
					})]
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "mt-1 h-2.5 w-full overflow-hidden rounded-full bg-slate-100",
					children: /* @__PURE__ */ (0, R.jsx)("div", {
						className: `h-full rounded-full ${r[n % r.length]}`,
						style: { width: `${a}%` }
					})
				})]
			}, e.status);
		})
	});
}
function wc({ position: e }) {
	let t = e.profit === null ? "text-slate-500" : e.profit >= 0 ? "text-emerald-700" : "text-red-700";
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		"data-testid": `ceo-finance-actual-${e.currency}`,
		"data-ceo-currency": e.currency,
		className: "min-w-0 rounded-2xl border border-emerald-200 bg-emerald-50/60 p-3.5 md:p-4",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex items-center justify-between gap-2",
				children: [/* @__PURE__ */ (0, R.jsx)("span", {
					className: "rounded-md bg-white/80 border border-slate-200 px-2 py-0.5 text-[12px] font-extrabold tracking-wide text-[#0f2a4a]",
					children: e.currency
				}), /* @__PURE__ */ (0, R.jsxs)("span", {
					className: "text-right text-[12px] leading-snug font-semibold text-slate-500",
					children: [bo(e.rowCount), " lô đã có Finance Actual"]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("dl", {
				className: "mt-3 space-y-2",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-baseline justify-between gap-2",
						children: [/* @__PURE__ */ (0, R.jsx)("dt", {
							className: "min-w-0 truncate text-[12.5px] font-semibold text-slate-600",
							children: "Doanh thu thực tế"
						}), /* @__PURE__ */ (0, R.jsx)("dd", {
							className: "shrink-0 text-[15px] font-extrabold text-[#0f2a4a]",
							children: G(e.revenueNet, e.currency)
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-baseline justify-between gap-2",
						children: [/* @__PURE__ */ (0, R.jsx)("dt", {
							className: "min-w-0 truncate text-[12.5px] font-semibold text-slate-600",
							children: "Chi phí thực tế"
						}), /* @__PURE__ */ (0, R.jsx)("dd", {
							className: "shrink-0 text-[15px] font-extrabold text-[#0f2a4a]",
							children: G(e.cost, e.currency)
						})]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex items-baseline justify-between gap-2 border-t border-emerald-200 pt-2",
						children: [/* @__PURE__ */ (0, R.jsx)("dt", {
							className: "min-w-0 truncate text-[12.5px] font-bold text-slate-700",
							children: "Lợi nhuận thực tế"
						}), /* @__PURE__ */ (0, R.jsx)("dd", {
							className: `shrink-0 text-[16px] font-extrabold ${t}`,
							children: G(e.profit, e.currency)
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-2 text-[12.5px] leading-relaxed text-slate-500",
				children: [
					"Biên lợi nhuận: ",
					/* @__PURE__ */ (0, R.jsx)("b", {
						className: "text-slate-700",
						children: _o(e.marginPct)
					}),
					" · tổng trong nội bộ ",
					e.currency,
					", không quy đổi"
				]
			}),
			e.incompleteRowCount > 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-1 text-[12.5px] font-semibold text-amber-800",
				children: [bo(e.incompleteRowCount), " dòng đã book nhưng chưa đủ số liệu an toàn, không tính là 0."]
			}) : null
		]
	});
}
function Tc({ group: e }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		"data-testid": `ceo-top-customers-${e.currency}`,
		"data-ceo-currency": e.currency,
		className: "min-w-0 rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5 md:p-4",
		children: [/* @__PURE__ */ (0, R.jsx)("span", {
			className: "rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[12px] font-extrabold tracking-wide text-[#0f2a4a]",
			children: e.currency
		}), /* @__PURE__ */ (0, R.jsx)("ol", {
			className: "mt-3 space-y-2",
			children: e.customers.map((t, n) => /* @__PURE__ */ (0, R.jsxs)("li", {
				className: "flex min-w-0 items-baseline justify-between gap-2",
				children: [/* @__PURE__ */ (0, R.jsxs)("span", {
					className: "min-w-0 truncate text-[13.5px] font-semibold text-slate-700",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("b", {
							className: "mr-1.5 text-[#1e5aa8]",
							children: [n + 1, "."]
						}),
						t.name,
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "ml-1.5 text-[12px] font-medium text-slate-400",
							children: [bo(t.shipmentCount), " lô"]
						})
					]
				}), /* @__PURE__ */ (0, R.jsx)("span", {
					className: "shrink-0 text-[13.5px] font-extrabold text-[#0f2a4a]",
					children: G(t.revenueNet, e.currency)
				})]
			}, `${t.name}-${n}`))
		})]
	});
}
function Ec({ item: e }) {
	let t = e.level === "Khan" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-900";
	return /* @__PURE__ */ (0, R.jsxs)(L, {
		to: e.route,
		"data-testid": "ceo-actionable-card",
		"data-ceo-shipment": e.shipmentId,
		className: "btn-press touch-target flex min-h-[52px] min-w-0 items-center justify-between gap-3 rounded-xl border-2 border-slate-200 bg-white px-3.5 py-2.5 hover:border-[#1e5aa8]",
		children: [/* @__PURE__ */ (0, R.jsxs)("span", {
			className: "min-w-0",
			children: [
				/* @__PURE__ */ (0, R.jsxs)("span", {
					className: "flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1",
					children: [
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: `rounded-md border px-1.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wide ${t}`,
							children: yc[e.level] ?? e.level
						}),
						/* @__PURE__ */ (0, R.jsx)("b", {
							className: "text-[14px] text-[#0f2a4a]",
							children: e.shipmentId
						}),
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: "truncate text-[12.5px] font-semibold text-slate-500",
							children: e.customer
						})
					]
				}),
				/* @__PURE__ */ (0, R.jsx)("span", {
					className: "mt-0.5 block truncate text-[13px] font-semibold text-slate-700",
					children: e.job
				}),
				e.detail ? /* @__PURE__ */ (0, R.jsx)("span", {
					className: "block truncate text-[12.5px] text-slate-500",
					children: e.detail
				}) : null
			]
		}), /* @__PURE__ */ (0, R.jsx)(gr, {
			size: 18,
			className: "shrink-0 text-[#1e5aa8]"
		})]
	});
}
function Dc() {
	let { ceoReport: e } = Jn();
	if (!e) return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "max-w-[1000px]",
		children: /* @__PURE__ */ (0, R.jsx)(Sc, { children: "Chưa nhận được tóm tắt quản trị từ nguồn Logistics. Hệ thống không hiển thị số liệu thay thế." })
	});
	let { operations: t, actionables: n, receivables: r, payables: i, financeActual: a, topCustomers: o, finance: s, reconciliation: c, quickLinks: l, unavailable: u } = e, d = c.obligations, f = c.money, p = !!(c.available && d && f), m = Math.max(t.actionableTaskCount - n.length, 0);
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-header",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(Ir, { size: 20 }),
					title: "Báo cáo CEO",
					sub: "Tóm tắt vị thế hiện tại từ dữ liệu Logistics đã có. Chỉ đọc; tiền tệ luôn tách riêng.",
					right: /* @__PURE__ */ (0, R.jsx)(q, {
						tone: "blue",
						size: "sm",
						children: "CHỈ ĐỌC"
					})
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "rounded-xl border border-blue-100 bg-blue-50 px-3.5 py-2.5 text-[13.5px] leading-relaxed text-blue-900",
					children: "Nhìn nhanh vận hành, công nợ, tài chính thực tế và điểm nghẽn cần xử lý. Không có biểu đồ xu hướng, kỳ so sánh hay số liệu ước tính."
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-operations",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(ra, { size: 20 }),
					title: "Vận hành",
					sub: "Đếm từ danh sách lô hiện tại và hàng đợi việc hiện có."
				}), /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
					"data-testid": "ceo-operations-cards",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-bold uppercase tracking-wide text-slate-500",
									children: "Tổng lô hàng"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
									children: bo(t.totalShipmentCount)
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[12.5px] text-slate-500",
									children: "Danh sách lô hiện tại"
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "min-w-0 rounded-2xl border border-blue-200 bg-blue-50 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-bold uppercase tracking-wide text-blue-700",
									children: "Lô đang chạy"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
									children: bo(t.openShipmentCount)
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[12.5px] text-blue-800",
									children: "Theo định nghĩa Tổng quan"
								})
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "min-w-0 rounded-2xl border border-amber-200 bg-amber-50 p-3.5",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[12px] font-bold uppercase tracking-wide text-amber-800",
									children: "Việc ưu tiên"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[26px] leading-tight font-extrabold text-[#0f2a4a]",
									children: bo(t.actionableTaskCount)
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-1 text-[12.5px] text-amber-900",
									children: "Khẩn + Cần xử lý"
								})
							]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
					"data-testid": "ceo-receivables",
					children: [/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(ro, {
							size: 20,
							className: "text-emerald-600"
						}),
						title: "Phải thu khách",
						sub: "C2C · chỉ tổng từ lô đã có Finance Actual."
					}), r.positions.length > 0 ? /* @__PURE__ */ (0, R.jsx)("div", {
						className: "grid gap-3 sm:grid-cols-2",
						"data-testid": "ceo-receivable-currency-grid",
						children: r.positions.map((e) => /* @__PURE__ */ (0, R.jsx)(bc, {
							position: e,
							kind: "receivable"
						}, e.currency))
					}) : /* @__PURE__ */ (0, R.jsxs)(Sc, { children: [
						"Chưa có tổng phải thu đủ điều kiện từ Finance Actual. Đây là trạng thái ",
						/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
						", không phải 0."
					] })]
				}), /* @__PURE__ */ (0, R.jsxs)("section", {
					className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
					"data-testid": "ceo-payables",
					children: [
						/* @__PURE__ */ (0, R.jsx)(J, {
							icon: /* @__PURE__ */ (0, R.jsx)(wi, {
								size: 20,
								className: "text-amber-700"
							}),
							title: "Phải trả đối tác",
							sub: "C2D · nghĩa vụ và phân bổ từ ledger canonical."
						}),
						i.error ? /* @__PURE__ */ (0, R.jsxs)(Sc, { children: [
							"Chưa đọc được ledger phải trả canonical: ",
							i.error,
							". Hệ thống không hiển thị số 0 thay thế."
						] }) : i.hasCanonicalRecords ? /* @__PURE__ */ (0, R.jsx)("div", {
							className: "grid gap-3 sm:grid-cols-2",
							"data-testid": "ceo-payable-currency-grid",
							children: i.positions.map((e) => /* @__PURE__ */ (0, R.jsx)(bc, {
								position: e,
								kind: "payable"
							}, e.currency))
						}) : /* @__PURE__ */ (0, R.jsxs)(Sc, { children: [
							"Chưa có bản ghi nghĩa vụ hoặc thanh toán canonical. Đây là trạng thái ",
							/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa có dữ liệu" }),
							", không phải phải trả bằng 0."
						] }),
						i.status === "REVIEW_REQUIRED" ? /* @__PURE__ */ (0, R.jsx)("p", {
							className: "mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900",
							children: "Có bản ghi phải trả cần rà soát trong desk đối soát."
						}) : null
					]
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-status-section",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(Ir, {
						size: 20,
						className: "text-[#1e5aa8]"
					}),
					title: "Trạng thái lô",
					sub: `Phân bổ theo ${bo(t.totalShipmentCount)} lô hiện tại — không kỳ, không ước tính.`
				}), t.statusCounts.length > 0 ? /* @__PURE__ */ (0, R.jsx)(Cc, {
					counts: t.statusCounts,
					total: t.totalShipmentCount
				}) : /* @__PURE__ */ (0, R.jsx)(Sc, { children: "Chưa có lô hàng trong dữ liệu hiện tại." })]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-finance-actual",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(ro, {
						size: 20,
						className: "text-emerald-700"
					}),
					title: "Tài chính thực tế",
					sub: "Doanh thu · chi phí · lợi nhuận đã book theo Finance Actual, tách riêng từng tiền tệ."
				}), a.available ? /* @__PURE__ */ (0, R.jsx)("div", {
					className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
					"data-testid": "ceo-finance-actual-grid",
					children: a.positions.map((e) => /* @__PURE__ */ (0, R.jsx)(wc, { position: e }, e.currency))
				}) : /* @__PURE__ */ (0, R.jsxs)(Sc, { children: [
					"Chưa có lô nào đủ Finance Actual để nêu vị thế tài chính thực tế. Đây là trạng thái ",
					/* @__PURE__ */ (0, R.jsx)("b", { children: "chưa xác định" }),
					", không phải doanh thu hay lợi nhuận bằng 0."
				] })]
			}),
			o.length > 0 ? /* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-top-customers",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(to, {
						size: 20,
						className: "text-[#1e5aa8]"
					}),
					title: "Top khách hàng",
					sub: "Xếp theo doanh thu thực tế trong nội bộ từng tiền tệ — không xếp chéo tiền tệ."
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
					"data-testid": "ceo-top-customers-grid",
					children: o.map((e) => /* @__PURE__ */ (0, R.jsx)(Tc, { group: e }, e.currency))
				})]
			}) : null,
			/* @__PURE__ */ (0, R.jsx)("section", {
				className: "rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/70 p-4 md:p-5",
				"data-testid": "ceo-finance-visibility",
				children: /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "flex items-start gap-3",
					children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
						size: 21,
						className: "mt-0.5 shrink-0 text-amber-700"
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "min-w-0",
						children: [/* @__PURE__ */ (0, R.jsx)("h3", {
							className: "text-[15px] font-extrabold text-amber-950",
							children: "Khả năng nhìn thấy tài chính"
						}), s.incompleteShipmentCount > 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "mt-1 text-[13.5px] leading-relaxed text-amber-900",
							children: [bo(s.incompleteShipmentCount), " lô chưa đủ Finance Actual. Các tổng tài chính phía trên không tính các lô này và không coi dữ liệu thiếu là 0."]
						}) : /* @__PURE__ */ (0, R.jsx)("p", {
							className: "mt-1 text-[13.5px] leading-relaxed text-amber-900",
							children: "Trang chỉ hiển thị các vị thế có nguồn hiện tại; không tự suy diễn thêm chỉ số tài chính."
						})]
					})]
				})
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-actionables",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(Ga, {
						size: 20,
						className: "text-red-600"
					}),
					title: "Điểm nghẽn cần xử lý",
					sub: "Việc Khẩn / Cần xử lý lấy từ dữ liệu lô và hàng đợi việc hiện có — bấm để mở đúng lô.",
					right: t.actionableTaskCount > 0 ? /* @__PURE__ */ (0, R.jsxs)(q, {
						tone: "red",
						size: "sm",
						children: [bo(t.actionableTaskCount), " VIỆC"]
					}) : void 0
				}), n.length > 0 ? /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "space-y-2.5",
					"data-testid": "ceo-actionable-list",
					children: [n.map((e) => /* @__PURE__ */ (0, R.jsx)(Ec, { item: e }, e.id)), m > 0 ? /* @__PURE__ */ (0, R.jsxs)(L, {
						to: "/viec-can-xu-ly",
						className: "flex min-h-[44px] min-w-0 items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-[13px] font-semibold text-slate-600 hover:border-[#1e5aa8]",
						children: [
							"Còn ",
							bo(m),
							" việc khác — mở desk việc cần xử lý",
							/* @__PURE__ */ (0, R.jsx)(gr, {
								size: 16,
								className: "text-[#1e5aa8]"
							})
						]
					}) : null]
				}) : /* @__PURE__ */ (0, R.jsx)(Sc, { children: "Hiện không có việc Khẩn hoặc Cần xử lý. Đây là trạng thái thật của hàng đợi việc hiện tại." })]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-reconciliation",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(Ca, {
							size: 20,
							className: "text-violet-700"
						}),
						title: "Đối soát",
						sub: "Số dòng theo trạng thái phân bổ từ ledger canonical; không phải đối soát sao kê hay sổ kế toán.",
						right: c.status === "REVIEW_REQUIRED" ? /* @__PURE__ */ (0, R.jsx)(q, {
							tone: "amber",
							size: "sm",
							children: "CẦN RÀ SOÁT"
						}) : void 0
					}),
					!c.available || !d || !f ? /* @__PURE__ */ (0, R.jsx)(Sc, { children: c.status === "NO_SOURCE" ? `Chưa đọc được ledger đối soát${c.error ? `: ${c.error}` : ""}. Không hiển thị số 0 thay thế.` : "Chưa có bản ghi đối soát canonical. Đây là trạng thái chưa có dữ liệu, không phải công nợ bằng 0." }) : /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "grid gap-3 lg:grid-cols-2",
						children: [/* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5",
							"data-testid": "ceo-reconciliation-obligations",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a]",
									children: "Nghĩa vụ"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-0.5 text-[12.5px] text-slate-500",
									children: "MATCHED / PARTIAL / UNMATCHED theo phân bổ đã có"
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4",
									children: [
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Đã đối soát",
											value: d.MATCHED,
											tone: "green"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Một phần",
											value: d.PARTIAL,
											tone: "amber"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Chưa đối soát",
											value: d.UNMATCHED,
											tone: "red"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Chưa xác định",
											value: d.UNKNOWN
										})
									]
								})
							]
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5",
							"data-testid": "ceo-reconciliation-money",
							children: [
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "text-[13px] font-extrabold text-[#0f2a4a]",
									children: "Giao dịch tiền"
								}),
								/* @__PURE__ */ (0, R.jsx)("p", {
									className: "mt-0.5 text-[12.5px] text-slate-500",
									children: "ALLOCATED / PARTIAL / UNALLOCATED theo phân bổ đã có"
								}),
								/* @__PURE__ */ (0, R.jsxs)("div", {
									className: "mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4",
									children: [
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Đã phân bổ",
											value: f.ALLOCATED,
											tone: "green"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Một phần",
											value: f.PARTIAL,
											tone: "amber"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Chưa phân bổ",
											value: f.UNALLOCATED,
											tone: "red"
										}),
										/* @__PURE__ */ (0, R.jsx)(xc, {
											label: "Chưa xác định",
											value: f.UNKNOWN
										})
									]
								})
							]
						})]
					}),
					p && c.reviewCount !== null && c.reviewCount > 0 ? /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "mt-3 inline-flex rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900",
						children: [bo(c.reviewCount), " dòng ledger cần rà soát."]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "ceo-quick-navigation",
				children: [/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(gr, { size: 20 }),
					title: "Đi nhanh tới dữ liệu gốc",
					sub: "Mỗi liên kết mở desk đã sở hữu dữ liệu và hành động nghiệp vụ tương ứng."
				}), /* @__PURE__ */ (0, R.jsx)("div", {
					className: "grid gap-2.5 sm:grid-cols-2",
					"data-testid": "ceo-quick-links",
					children: l.map((e) => /* @__PURE__ */ (0, R.jsxs)(L, {
						to: e.href,
						className: "btn-press touch-target flex min-h-[52px] min-w-0 items-center justify-between gap-3 rounded-xl border-2 border-slate-200 bg-white px-4 py-2.5 text-left hover:border-[#1e5aa8]",
						children: [/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "min-w-0",
							children: [/* @__PURE__ */ (0, R.jsx)("span", {
								className: "block text-[14px] font-extrabold text-[#0f2a4a]",
								children: e.label
							}), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "block truncate text-[12.5px] text-slate-500",
								children: e.note
							})]
						}), /* @__PURE__ */ (0, R.jsx)(gr, {
							size: 18,
							className: "shrink-0 text-[#1e5aa8]"
						})]
					}, e.href))
				})]
			}),
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-slate-50 p-4",
				"data-testid": "ceo-scope-note",
				children: [/* @__PURE__ */ (0, R.jsx)("p", {
					className: "text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
					children: "Phạm vi dữ liệu"
				}), /* @__PURE__ */ (0, R.jsx)("ul", {
					className: "mt-2 space-y-1.5 text-[13.5px] leading-relaxed text-slate-600",
					children: u.map((e) => /* @__PURE__ */ (0, R.jsxs)("li", { children: ["• ", e] }, e))
				})]
			})
		]
	});
}
//#endregion
//#region src/pages/Notebook.tsx
function Oc(e, t) {
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
function kc(e) {
	return /^https:\/\//i.test(e.trim());
}
function Ac({ provenance: e }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		"data-testid": "handbook-provenance",
		className: "rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-[12.5px] leading-relaxed text-slate-600",
		children: [
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "font-bold uppercase tracking-wide text-slate-500",
				children: "Nguồn"
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-1 break-words font-mono text-[12px] text-[#0f2a4a]",
				children: e.source
			}),
			/* @__PURE__ */ (0, R.jsxs)("ul", {
				className: "mt-1 space-y-0.5",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("li", { children: [
						"Phiên bản:",
						" ",
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: "font-semibold",
							children: e.version ?? "không có trong nguồn"
						})
					] }),
					/* @__PURE__ */ (0, R.jsxs)("li", { children: [
						"Cập nhật:",
						" ",
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: "font-semibold",
							children: e.updated ?? "không có trong nguồn"
						})
					] }),
					/* @__PURE__ */ (0, R.jsxs)("li", { children: [
						"Phụ trách:",
						" ",
						/* @__PURE__ */ (0, R.jsx)("span", {
							className: "font-semibold",
							children: e.owner ?? "không có trong nguồn"
						})
					] })
				]
			}),
			e.note ? /* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-1.5 border-t border-slate-200 pt-1.5 text-slate-500",
				children: e.note
			}) : null
		]
	});
}
function jc({ table: e }) {
	let t = e.columns.length <= 2 || e.columns.some((e) => /url|link/i.test(e)), n = (e) => t && kc(e) ? /* @__PURE__ */ (0, R.jsxs)("a", {
		href: e,
		target: "_blank",
		rel: "noreferrer",
		className: "inline-flex max-w-full items-start gap-1 break-all font-semibold text-blue-800 underline decoration-blue-300 underline-offset-2",
		children: [/* @__PURE__ */ (0, R.jsx)(fi, {
			size: 13,
			className: "mt-0.5 shrink-0"
		}), /* @__PURE__ */ (0, R.jsx)("span", {
			className: "break-all",
			children: e
		})]
	}) : /* @__PURE__ */ (0, R.jsx)("span", {
		className: "break-words",
		children: e
	});
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "mt-3",
		children: [
			/* @__PURE__ */ (0, R.jsx)("div", {
				className: "space-y-2 md:hidden",
				children: e.rows.map((t, r) => /* @__PURE__ */ (0, R.jsx)("div", {
					className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
					"data-testid": "handbook-row-mobile",
					children: t.map((t, r) => /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "py-0.5 text-[13.5px] leading-relaxed",
						children: [/* @__PURE__ */ (0, R.jsx)("span", {
							className: "mr-1.5 text-[11.5px] font-bold uppercase tracking-wide text-slate-500",
							children: e.columns[r] ?? ""
						}), n(t)]
					}, `c-${r}`))
				}, `m-${r}`))
			}),
			/* @__PURE__ */ (0, R.jsxs)("table", {
				className: "hidden w-full border-collapse md:table",
				children: [/* @__PURE__ */ (0, R.jsx)("thead", { children: /* @__PURE__ */ (0, R.jsx)("tr", {
					className: "bg-slate-50",
					children: e.columns.map((e, t) => /* @__PURE__ */ (0, R.jsx)("th", {
						scope: "col",
						className: "border-b border-slate-200 px-2.5 py-2 text-left text-[11.5px] font-extrabold uppercase tracking-wide text-slate-500",
						children: e
					}, `h-${t}`))
				}) }), /* @__PURE__ */ (0, R.jsx)("tbody", { children: e.rows.map((e, t) => /* @__PURE__ */ (0, R.jsx)("tr", {
					className: "align-top odd:bg-white even:bg-slate-50/50",
					children: e.map((e, t) => /* @__PURE__ */ (0, R.jsx)("td", {
						className: "border-b border-slate-100 px-2.5 py-2 text-[13.5px] leading-relaxed text-slate-700",
						children: n(e)
					}, `d-${t}`))
				}, `r-${t}`)) })]
			}),
			/* @__PURE__ */ (0, R.jsxs)("p", {
				className: "mt-1.5 text-[12px] text-slate-400",
				children: [e.rows.length, " dòng · đọc từ nguồn, không phải dữ liệu mẫu"]
			})
		]
	});
}
function Mc({ section: e, entry: t, onBack: n }) {
	let r = So[e.icon] ?? Ar;
	return /* @__PURE__ */ (0, R.jsxs)("article", {
		className: "space-y-3",
		"data-testid": "handbook-article",
		"data-article-id": t.id,
		children: [
			/* @__PURE__ */ (0, R.jsxs)("button", {
				type: "button",
				onClick: n,
				className: "btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 bg-white px-3.5 py-2 text-[13.5px] font-bold text-[#0f2a4a]",
				"data-testid": "handbook-back",
				children: [/* @__PURE__ */ (0, R.jsx)(mr, { size: 17 }), " Về danh mục"]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("p", {
						className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
						children: [
							/* @__PURE__ */ (0, R.jsx)(r, {
								size: 15,
								className: "shrink-0"
							}),
							" ",
							e.label
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("h3", {
						className: "mt-2 break-words text-[19px] leading-snug font-extrabold text-[#0f2a4a] md:text-[21px]",
						children: t.title
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "mt-1.5 text-[14px] leading-relaxed text-slate-600",
						children: t.summary
					}),
					t.bullets.length > 0 ? /* @__PURE__ */ (0, R.jsx)("ul", {
						className: "mt-3 space-y-1.5",
						children: t.bullets.map((e, t) => /* @__PURE__ */ (0, R.jsxs)("li", {
							className: "flex gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[13.5px] leading-relaxed text-slate-700",
							children: [/* @__PURE__ */ (0, R.jsx)("span", {
								className: "mt-0.5 text-slate-400",
								children: "•"
							}), /* @__PURE__ */ (0, R.jsx)("span", {
								className: "min-w-0 break-words",
								children: e
							})]
						}, t))
					}) : null,
					t.table ? /* @__PURE__ */ (0, R.jsx)(jc, { table: t.table }) : null,
					t.tags.length > 0 ? /* @__PURE__ */ (0, R.jsx)("p", {
						className: "mt-3 flex flex-wrap gap-1.5",
						children: t.tags.map((e) => /* @__PURE__ */ (0, R.jsxs)("span", {
							className: "rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600",
							children: ["#", e]
						}, e))
					}) : null,
					t.links.length > 0 ? /* @__PURE__ */ (0, R.jsx)("div", {
						className: "mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3",
						children: t.links.map((e) => /* @__PURE__ */ (0, R.jsxs)(L, {
							to: e.href,
							className: "btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] px-3.5 py-2 text-[13.5px] font-bold text-white",
							children: [
								e.label,
								" ",
								/* @__PURE__ */ (0, R.jsx)(gr, { size: 15 })
							]
						}, e.href))
					}) : null
				]
			}),
			/* @__PURE__ */ (0, R.jsx)(Ac, { provenance: t.provenance ?? e.provenance })
		]
	});
}
function Nc({ section: e, entry: t, onOpen: n }) {
	return /* @__PURE__ */ (0, R.jsxs)("button", {
		type: "button",
		onClick: n,
		"data-testid": "handbook-entry",
		"data-entry-id": t.id,
		className: "btn-press w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-blue-300",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "flex items-start justify-between gap-3",
				children: [/* @__PURE__ */ (0, R.jsx)("h4", {
					className: "min-w-0 break-words text-[15.5px] leading-snug font-extrabold text-[#0f2a4a]",
					children: t.title
				}), /* @__PURE__ */ (0, R.jsx)(gr, {
					size: 18,
					className: "mt-0.5 shrink-0 text-slate-400"
				})]
			}),
			/* @__PURE__ */ (0, R.jsx)("p", {
				className: "mt-1.5 text-[13.5px] leading-relaxed text-slate-600",
				children: t.summary
			}),
			t.table && t.table.rows.length > 0 ? /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "mt-2 space-y-1",
				"data-testid": "handbook-preview",
				children: [t.table.rows.slice(0, 2).map((e, t) => /* @__PURE__ */ (0, R.jsx)("p", {
					className: "break-words rounded-lg bg-slate-50 px-2 py-1 font-mono text-[12px] text-slate-600",
					children: e.filter((e) => e.trim() !== "").join(" · ")
				}, t)), t.table.rows.length > 2 ? /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[12px] font-semibold text-slate-400",
					children: [
						"+",
						t.table.rows.length - 2,
						" dòng nữa trong bài"
					]
				}) : null]
			}) : null,
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "mt-2.5 flex flex-wrap items-center gap-2",
				children: [
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-600",
						children: e.label
					}),
					t.table ? /* @__PURE__ */ (0, R.jsxs)("span", {
						className: "rounded-md bg-blue-50 px-2 py-0.5 text-[11.5px] font-bold text-blue-800",
						children: [t.table.rows.length, " dòng"]
					}) : null,
					/* @__PURE__ */ (0, R.jsx)("span", {
						className: "text-[11.5px] font-semibold text-slate-400",
						children: t.tags.slice(0, 3).map((e) => `#${e}`).join(" ")
					})
				]
			})
		]
	});
}
function Pc({ reason: e }) {
	return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "max-w-[760px]",
		children: /* @__PURE__ */ (0, R.jsx)("div", {
			className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
			children: e === "pending" ? "Chưa nhận được dữ liệu Sổ tay từ backend. Trang không hiển thị nội dung mẫu thay thế." : "Nguồn tham chiếu chưa trả về mục nào có nội dung. Sổ tay hiển thị đúng trạng thái này thay vì tự soạn bài."
		})
	});
}
function Fc() {
	let { handbook: e } = Jn(), [t, n] = (0, _.useState)(null), [r, i] = (0, _.useState)(null), [a, o] = (0, _.useState)(""), s = a.trim().toLowerCase(), c = (0, _.useMemo)(() => {
		let t = [];
		for (let n of e?.sections ?? []) for (let e of n.entries) t.push({
			section: n,
			entry: e,
			hay: Oc(n, e)
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
	if (!e) return /* @__PURE__ */ (0, R.jsx)(Pc, { reason: "pending" });
	let d = e;
	if (d.counts.entryCount === 0 && !s) return /* @__PURE__ */ (0, R.jsx)(Pc, { reason: "no-source" });
	let f = d.sections.find((e) => e.id === t) ?? null, p = d.sections.filter((e) => e.state && e.entries.length === 0), m = (e) => {
		i(e), typeof window < "u" && window.scrollTo({
			top: 0,
			behavior: "auto"
		});
	}, h = () => i(null), g = (e) => {
		n(e === t ? null : e), i(null), o("");
	};
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [/* @__PURE__ */ (0, R.jsxs)("section", {
			className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
			"data-testid": "handbook-header",
			children: [
				/* @__PURE__ */ (0, R.jsx)(J, {
					icon: /* @__PURE__ */ (0, R.jsx)(Ar, { size: 20 }),
					title: "Sổ tay vận hành",
					sub: "Tra cứu quy trình, chứng từ, mã dịch vụ và phân quyền — đúng theo tài liệu hệ thống đang dùng.",
					right: /* @__PURE__ */ (0, R.jsx)(q, {
						tone: "blue",
						size: "sm",
						children: "CHỈ ĐỌC"
					})
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [
								d.counts.availableSectionCount,
								"/",
								d.counts.sectionCount,
								" mục có nội dung"
							]
						}),
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							children: [d.counts.entryCount, " bài tham chiếu"]
						}),
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "rounded-lg bg-slate-100 px-2 py-1",
							"data-testid": "handbook-note-count",
							children: [d.counts.noteTotal ?? d.counts.noteCount, " ghi chú đội ngũ"]
						}),
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800",
							children: [
								/* @__PURE__ */ (0, R.jsx)(ka, { size: 13 }),
								" ",
								d.readOnly ? "không sửa từ trang này" : "có chỉnh sửa"
							]
						})
					]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "relative mt-3",
					children: [
						/* @__PURE__ */ (0, R.jsx)(Ta, {
							size: 17,
							className: "pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
						}),
						/* @__PURE__ */ (0, R.jsx)("input", {
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
						a ? /* @__PURE__ */ (0, R.jsx)("button", {
							type: "button",
							onClick: () => o(""),
							"aria-label": "Xóa từ khóa",
							className: "touch-target absolute right-1 top-1/2 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-xl text-slate-400 hover:bg-slate-100",
							children: /* @__PURE__ */ (0, R.jsx)(ao, { size: 17 })
						}) : null
					]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex flex-wrap gap-2",
					"data-testid": "handbook-categories",
					children: [/* @__PURE__ */ (0, R.jsx)("button", {
						type: "button",
						onClick: () => {
							n(null), i(null), o("");
						},
						className: U("min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors", t === null ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"),
						"data-testid": "handbook-category-all",
						children: "Tất cả"
					}), d.sections.map((e) => /* @__PURE__ */ (0, R.jsxs)("button", {
						type: "button",
						onClick: () => g(e.id),
						className: U("min-h-[44px] rounded-xl border px-3 py-2 text-[13px] font-bold transition-colors", e.id === t ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-[#0f2a4a] hover:border-blue-300"),
						"data-testid": `handbook-category-${e.id}`,
						children: [e.label, /* @__PURE__ */ (0, R.jsx)("span", {
							className: "ml-1.5 text-[11.5px] font-extrabold opacity-70",
							children: e.entries.length
						})]
					}, e.id))]
				})
			]
		}), u ? /* @__PURE__ */ (0, R.jsx)(Mc, {
			section: u.section,
			entry: u.entry,
			onBack: h
		}) : /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]",
			children: [/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "min-w-0 space-y-2.5",
				children: [f && !s ? /* @__PURE__ */ (0, R.jsxs)("p", {
					className: "text-[13px] leading-relaxed text-slate-500",
					"data-testid": "handbook-section-lead",
					children: [
						/* @__PURE__ */ (0, R.jsxs)("span", {
							className: "font-extrabold text-[#0f2a4a]",
							children: [f.label, ":"]
						}),
						" ",
						f.lead
					]
				}) : null, l.length === 0 ? /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
					"data-testid": "handbook-no-result",
					children: [
						"Không có bài nào khớp “",
						a,
						"”. Sổ tay chỉ tìm trong nội dung đã có trong nguồn và không tạo bài mới."
					]
				}) : l.map(({ section: e, entry: t }) => /* @__PURE__ */ (0, R.jsx)(Nc, {
					section: e,
					entry: t,
					onOpen: () => m(t.id)
				}, `${e.id}-${t.id}`))]
			}), /* @__PURE__ */ (0, R.jsxs)("aside", {
				className: "min-w-0 space-y-3",
				children: [
					f && !s ? /* @__PURE__ */ (0, R.jsx)(Ac, { provenance: f.provenance }) : null,
					p.length > 0 ? /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5",
						"data-testid": "handbook-empty-sections",
						children: [/* @__PURE__ */ (0, R.jsx)("p", {
							className: "text-[12px] font-extrabold uppercase tracking-wide text-amber-800",
							children: "Mục chưa có nguồn"
						}), /* @__PURE__ */ (0, R.jsx)("ul", {
							className: "mt-1 space-y-1 text-[13px] leading-relaxed text-amber-900",
							children: p.map((e) => /* @__PURE__ */ (0, R.jsxs)("li", { children: [
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-bold",
									children: e.label
								}),
								" — ",
								e.state?.text
							] }, e.id))
						})]
					}) : null,
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
						children: [/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, R.jsx)(Ai, { size: 14 }), " Trang này không có"]
						}), /* @__PURE__ */ (0, R.jsx)("ul", {
							className: "mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600",
							children: d.unavailable.map((e) => /* @__PURE__ */ (0, R.jsx)("li", {
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
function Ic(e) {
	return oo[e.toUpperCase()] ?? e;
}
function Lc(e) {
	switch (e.toLowerCase()) {
		case "admin": return "red";
		case "support": return "blue";
		case "sale": return "green";
		default: return "gray";
	}
}
function Rc(e) {
	return (e.trim().split(/\s+/).slice(0, 2).map((e) => [...e][0] ?? "").join("") || "?").toUpperCase();
}
function zc(e) {
	return `${e}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}
function Bc({ name: e }) {
	return /* @__PURE__ */ (0, R.jsx)("span", {
		className: "break-all rounded-md bg-slate-100 px-2 py-1 font-mono text-[11.5px] font-semibold text-slate-700",
		"data-testid": "user-access-permission",
		children: e
	});
}
function Vc({ assignableRoles: e, onClose: t, lastWrites: n, onSuccess: r }) {
	let [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)(""), [u, d] = (0, _.useState)(e[0] ?? ""), [f, p] = (0, _.useState)(""), [m, h] = (0, _.useState)(""), [g, v] = (0, _.useState)(""), [y, b] = (0, _.useState)(""), [x, S] = (0, _.useState)(null);
	return (0, _.useEffect)(() => {
		if (!x) return;
		let e = n.find((e) => e.event === "user_create" && e.requestId === x.requestId);
		if (e) {
			if (e.ok) {
				let e = x.username;
				S(null), p(""), h(""), r(e);
			} else S(null), b(e.error || "Backend từ chối tạo tài khoản.");
		}
	}, [n, x]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "fixed inset-0 z-50 flex items-end justify-center sm:items-center",
		id: "user-create-sheet",
		children: [/* @__PURE__ */ (0, R.jsx)("div", {
			className: "absolute inset-0 bg-black/40",
			onClick: () => !x && t()
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "relative w-full max-w-[520px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5",
			children: [
				/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]",
					children: [/* @__PURE__ */ (0, R.jsx)($a, { size: 18 }), " Thêm tài khoản"]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 space-y-3",
					children: [
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Tên đăng nhập",
							required: !0,
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: i,
								onChange: (e) => {
									a(e.target.value), v("");
								},
								placeholder: "vd: lan.sale",
								className: X(i.trim() ? "ok" : "missing")
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Tên hiển thị",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: o,
								onChange: (e) => s(e.target.value),
								placeholder: "vd: Lan Sale",
								className: X()
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Email (không bắt buộc)",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								value: c,
								onChange: (e) => l(e.target.value),
								placeholder: "vd: lan.sale@congty.vn",
								className: X()
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Vai trò",
							required: !0,
							children: /* @__PURE__ */ (0, R.jsx)("select", {
								value: u,
								onChange: (e) => d(e.target.value),
								className: X(),
								children: e.map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
									value: e,
									children: Ic(e)
								}, e))
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Mật khẩu",
							required: !0,
							hint: "Tối thiểu 8 ký tự.",
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								type: "password",
								value: f,
								onChange: (e) => {
									p(e.target.value), v("");
								},
								className: X(),
								autoComplete: "new-password"
							})
						}),
						/* @__PURE__ */ (0, R.jsx)(Y, {
							label: "Xác nhận mật khẩu",
							required: !0,
							children: /* @__PURE__ */ (0, R.jsx)("input", {
								type: "password",
								value: m,
								onChange: (e) => {
									h(e.target.value), v("");
								},
								className: X(),
								autoComplete: "new-password"
							})
						})
					]
				}),
				(g || y) && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700",
					role: "alert",
					id: "user-create-error",
					children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
						size: 16,
						className: "mt-0.5 shrink-0"
					}), /* @__PURE__ */ (0, R.jsx)("span", {
						className: "break-words",
						children: y || g
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-4 flex gap-2.5",
					children: [/* @__PURE__ */ (0, R.jsx)(wo, {
						onClick: () => {
							if (x) return;
							let e = i.trim();
							if (!e) {
								v("Nhập tên đăng nhập.");
								return;
							}
							if (!u) {
								v("Chọn vai trò.");
								return;
							}
							if (!f || f.length < 8) {
								v("Mật khẩu phải có ít nhất 8 ký tự.");
								return;
							}
							if (f !== m) {
								v("Mật khẩu xác nhận không khớp.");
								return;
							}
							let t = zc("USER-CREATE-REQ");
							if (!A("user_create", {
								username: e,
								displayName: o.trim(),
								email: c.trim(),
								role: u,
								password: f,
								confirmPassword: m,
								active: !0,
								requestId: t
							})) {
								v("Component chưa kết nối backend — chưa gửi được yêu cầu.");
								return;
							}
							v(""), b(""), S({
								requestId: t,
								username: e
							});
						},
						disabled: !!x,
						className: "flex-1",
						children: x ? "ĐANG TẠO…" : "TẠO TÀI KHOẢN"
					}), /* @__PURE__ */ (0, R.jsx)(Eo, {
						onClick: () => !x && t(),
						className: "min-w-[96px]",
						children: "Hủy"
					})]
				})
			]
		})]
	});
}
function Hc({ account: e, assignableRoles: t, onClose: n, lastWrites: r, onSuccess: i }) {
	let [a, o] = (0, _.useState)(e.role), [s, c] = (0, _.useState)(""), [l, u] = (0, _.useState)(null);
	return (0, _.useEffect)(() => {
		if (!l) return;
		let e = r.find((e) => e.event === "user_role_set" && e.requestId === l);
		e && (e.ok ? (u(null), i()) : (u(null), c(e.error || "Backend từ chối đổi vai trò.")));
	}, [r, l]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "fixed inset-0 z-50 flex items-end justify-center sm:items-center",
		id: "user-role-sheet",
		children: [/* @__PURE__ */ (0, R.jsx)("div", {
			className: "absolute inset-0 bg-black/40",
			onClick: () => !l && n()
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5",
			children: [
				/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]",
					children: [
						/* @__PURE__ */ (0, R.jsx)(Za, { size: 18 }),
						" Đổi vai trò — ",
						e.display_name || e.username
					]
				}),
				/* @__PURE__ */ (0, R.jsx)("p", {
					className: "mt-1 break-all font-mono text-[12px] text-slate-500",
					children: e.username
				}),
				/* @__PURE__ */ (0, R.jsx)("div", {
					className: "mt-3",
					children: /* @__PURE__ */ (0, R.jsx)(Y, {
						label: "Vai trò mới",
						required: !0,
						children: /* @__PURE__ */ (0, R.jsx)("select", {
							value: a,
							onChange: (e) => o(e.target.value),
							className: X(),
							children: t.map((e) => /* @__PURE__ */ (0, R.jsx)("option", {
								value: e,
								children: Ic(e)
							}, e))
						})
					})
				}),
				s && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700",
					role: "alert",
					id: "user-role-error",
					children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
						size: 16,
						className: "mt-0.5 shrink-0"
					}), /* @__PURE__ */ (0, R.jsx)("span", {
						className: "break-words",
						children: s
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-4 flex gap-2.5",
					children: [/* @__PURE__ */ (0, R.jsx)(wo, {
						onClick: () => {
							if (l) return;
							let t = zc("USER-ROLE-REQ");
							if (!A("user_role_set", {
								username: e.username,
								role: a,
								requestId: t
							})) {
								c("Component chưa kết nối backend.");
								return;
							}
							c(""), u(t);
						},
						disabled: !!l,
						className: "flex-1",
						children: l ? "ĐANG LƯU…" : "LƯU VAI TRÒ"
					}), /* @__PURE__ */ (0, R.jsx)(Eo, {
						onClick: () => !l && n(),
						className: "min-w-[96px]",
						children: "Hủy"
					})]
				})
			]
		})]
	});
}
function Uc({ account: e, onClose: t, lastWrites: n, onSuccess: r }) {
	let i = !e.active, [a, o] = (0, _.useState)(""), [s, c] = (0, _.useState)(null);
	return (0, _.useEffect)(() => {
		if (!s) return;
		let e = n.find((e) => e.event === "user_active_set" && e.requestId === s);
		e && (e.ok ? (c(null), r()) : (c(null), o(e.error || "Backend từ chối cập nhật trạng thái.")));
	}, [n, s]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "fixed inset-0 z-50 flex items-end justify-center sm:items-center",
		id: "user-active-sheet",
		children: [/* @__PURE__ */ (0, R.jsx)("div", {
			className: "absolute inset-0 bg-black/40",
			onClick: () => !s && t()
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5",
			children: [
				/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]",
					children: [
						i ? /* @__PURE__ */ (0, R.jsx)(Gi, { size: 18 }) : /* @__PURE__ */ (0, R.jsx)(qi, { size: 18 }),
						" ",
						i ? "Kích hoạt lại" : "Vô hiệu hóa",
						" — ",
						e.display_name || e.username
					]
				}),
				/* @__PURE__ */ (0, R.jsx)("p", {
					className: "mt-2 text-[13.5px] leading-relaxed text-slate-600",
					children: i ? "Tài khoản sẽ đăng nhập được trở lại ngay sau khi máy chủ xác nhận." : "Tài khoản sẽ không đăng nhập được nữa. Lịch sử tài khoản vẫn được giữ nguyên — đây không phải xóa tài khoản."
				}),
				a && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700",
					role: "alert",
					id: "user-active-error",
					children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
						size: 16,
						className: "mt-0.5 shrink-0"
					}), /* @__PURE__ */ (0, R.jsx)("span", {
						className: "break-words",
						children: a
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-4 flex gap-2.5",
					children: [/* @__PURE__ */ (0, R.jsx)(wo, {
						onClick: () => {
							if (s) return;
							let t = zc("USER-ACTIVE-REQ");
							if (!A("user_active_set", {
								username: e.username,
								active: i,
								requestId: t
							})) {
								o("Component chưa kết nối backend.");
								return;
							}
							o(""), c(t);
						},
						disabled: !!s,
						className: "flex-1",
						children: s ? "ĐANG LƯU…" : i ? "KÍCH HOẠT LẠI" : "VÔ HIỆU HÓA"
					}), /* @__PURE__ */ (0, R.jsx)(Eo, {
						onClick: () => !s && t(),
						className: "min-w-[96px]",
						children: "Hủy"
					})]
				})
			]
		})]
	});
}
function Wc({ account: e, onClose: t, lastWrites: n, onSuccess: r }) {
	let [i, a] = (0, _.useState)(""), [o, s] = (0, _.useState)(""), [c, l] = (0, _.useState)(""), [u, d] = (0, _.useState)(""), [f, p] = (0, _.useState)(null);
	return (0, _.useEffect)(() => {
		if (!f) return;
		let e = n.find((e) => e.event === "user_password_reset" && e.requestId === f);
		e && (e.ok ? (p(null), a(""), s(""), r()) : (p(null), d(e.error || "Backend từ chối đặt lại mật khẩu.")));
	}, [n, f]), /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "fixed inset-0 z-50 flex items-end justify-center sm:items-center",
		id: "user-password-sheet",
		children: [/* @__PURE__ */ (0, R.jsx)("div", {
			className: "absolute inset-0 bg-black/40",
			onClick: () => !f && t()
		}), /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "relative w-full max-w-[440px] rounded-t-2xl bg-white p-4 sm:rounded-2xl md:p-5",
			children: [
				/* @__PURE__ */ (0, R.jsxs)("p", {
					className: "flex items-center gap-2 text-[16px] font-extrabold text-[#0f2a4a]",
					children: [
						/* @__PURE__ */ (0, R.jsx)(ya, { size: 18 }),
						" Đặt mật khẩu mới — ",
						e.display_name || e.username
					]
				}),
				/* @__PURE__ */ (0, R.jsx)("p", {
					className: "mt-1 text-[12.5px] leading-relaxed text-slate-500",
					children: "Đặt trực tiếp mật khẩu mới cho tài khoản này (không gửi email, không tạo đường dẫn đặt lại)."
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 space-y-3",
					children: [/* @__PURE__ */ (0, R.jsx)(Y, {
						label: "Mật khẩu mới",
						required: !0,
						hint: "Tối thiểu 8 ký tự.",
						children: /* @__PURE__ */ (0, R.jsx)("input", {
							type: "password",
							value: i,
							onChange: (e) => {
								a(e.target.value), l("");
							},
							className: X(),
							autoComplete: "new-password"
						})
					}), /* @__PURE__ */ (0, R.jsx)(Y, {
						label: "Xác nhận mật khẩu mới",
						required: !0,
						children: /* @__PURE__ */ (0, R.jsx)("input", {
							type: "password",
							value: o,
							onChange: (e) => {
								s(e.target.value), l("");
							},
							className: X(),
							autoComplete: "new-password"
						})
					})]
				}),
				(c || u) && /* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-3 flex items-start gap-2 rounded-xl border-2 border-red-200 bg-red-50 p-3 text-[13px] font-semibold text-red-700",
					role: "alert",
					id: "user-password-error",
					children: [/* @__PURE__ */ (0, R.jsx)(Wr, {
						size: 16,
						className: "mt-0.5 shrink-0"
					}), /* @__PURE__ */ (0, R.jsx)("span", {
						className: "break-words",
						children: u || c
					})]
				}),
				/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "mt-4 flex gap-2.5",
					children: [/* @__PURE__ */ (0, R.jsx)(wo, {
						onClick: () => {
							if (f) return;
							if (!i || i.length < 8) {
								l("Mật khẩu mới phải có ít nhất 8 ký tự.");
								return;
							}
							if (i !== o) {
								l("Mật khẩu xác nhận không khớp.");
								return;
							}
							let t = zc("USER-PWD-REQ");
							if (!A("user_password_reset", {
								username: e.username,
								newPassword: i,
								confirmPassword: o,
								requestId: t
							})) {
								l("Component chưa kết nối backend.");
								return;
							}
							l(""), d(""), p(t);
						},
						disabled: !!f,
						className: "flex-1",
						children: f ? "ĐANG LƯU…" : "ĐẶT MẬT KHẨU MỚI"
					}), /* @__PURE__ */ (0, R.jsx)(Eo, {
						onClick: () => !f && t(),
						className: "min-w-[96px]",
						children: "Hủy"
					})]
				})
			]
		})]
	});
}
function Gc({ account: e, canManage: t, onManageRole: n, onManageActive: r, onManagePassword: i }) {
	let a = e.display_name || e.username;
	return /* @__PURE__ */ (0, R.jsx)("div", {
		"data-testid": "user-access-account",
		"data-username": e.username,
		"data-role": e.role,
		className: "w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5",
		children: /* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex items-start gap-3",
			children: [/* @__PURE__ */ (0, R.jsx)("span", {
				className: U("grid h-10 w-10 shrink-0 place-items-center rounded-xl text-[14px] font-extrabold", e.active ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-400"),
				"aria-hidden": !0,
				children: Rc(a)
			}), /* @__PURE__ */ (0, R.jsxs)("div", {
				className: "min-w-0 flex-1",
				children: [
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "flex flex-wrap items-center gap-x-2 gap-y-1",
						children: [
							/* @__PURE__ */ (0, R.jsx)("p", {
								className: "min-w-0 break-words text-[15px] font-extrabold text-[#0f2a4a]",
								children: a
							}),
							/* @__PURE__ */ (0, R.jsx)(q, {
								tone: Lc(e.role),
								size: "sm",
								children: Ic(e.role)
							}),
							e.active ? /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11.5px] font-bold text-emerald-800",
								"data-testid": "user-access-account-active",
								children: [/* @__PURE__ */ (0, R.jsx)(br, { size: 12 }), " Hoạt động"]
							}) : /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11.5px] font-bold text-slate-500",
								"data-testid": "user-access-account-inactive",
								children: [/* @__PURE__ */ (0, R.jsx)(qi, { size: 12 }), " Đã vô hiệu hóa"]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsx)("p", {
						className: "mt-1 break-all font-mono text-[12px] text-slate-500",
						children: e.username
					}),
					e.email ? /* @__PURE__ */ (0, R.jsx)("p", {
						className: "mt-0.5 min-w-0 break-all text-[12.5px] text-slate-500",
						children: e.email
					}) : null,
					e.user_id ? /* @__PURE__ */ (0, R.jsxs)("p", {
						className: "mt-1 break-all font-mono text-[11px] text-slate-400",
						children: ["ID: ", e.user_id]
					}) : null,
					t && /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-2.5 flex flex-wrap gap-2",
						"data-testid": "user-access-account-actions",
						children: [
							/* @__PURE__ */ (0, R.jsxs)(Eo, {
								onClick: n,
								className: "min-h-[36px] px-3 text-[13px]",
								children: [/* @__PURE__ */ (0, R.jsx)(Za, { size: 14 }), " Đổi vai trò"]
							}),
							/* @__PURE__ */ (0, R.jsxs)(Eo, {
								onClick: r,
								className: "min-h-[36px] px-3 text-[13px]",
								danger: e.active,
								children: [e.active ? /* @__PURE__ */ (0, R.jsx)(qi, { size: 14 }) : /* @__PURE__ */ (0, R.jsx)(Gi, { size: 14 }), e.active ? "Vô hiệu hóa" : "Kích hoạt lại"]
							}),
							/* @__PURE__ */ (0, R.jsxs)(Eo, {
								onClick: i,
								className: "min-h-[36px] px-3 text-[13px]",
								children: [/* @__PURE__ */ (0, R.jsx)(ya, { size: 14 }), " Đặt mật khẩu mới"]
							})
						]
					})
				]
			})]
		})
	});
}
function Kc({ row: e, assignable: t }) {
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		"data-testid": "user-access-role-row",
		"data-role": e.role,
		className: "w-full min-w-0 rounded-2xl border border-slate-200 bg-white p-3.5",
		children: [/* @__PURE__ */ (0, R.jsxs)("div", {
			className: "flex flex-wrap items-center gap-2",
			children: [
				/* @__PURE__ */ (0, R.jsx)(q, {
					tone: Lc(e.role),
					size: "sm",
					children: Ic(e.role)
				}),
				e.wildcard ? /* @__PURE__ */ (0, R.jsxs)("span", {
					className: "inline-flex items-center gap-1 rounded-md bg-violet-50 px-2 py-0.5 text-[11.5px] font-bold text-violet-800",
					children: [/* @__PURE__ */ (0, R.jsx)(Mi, { size: 12 }), " * = toàn quyền"]
				}) : null,
				t ? /* @__PURE__ */ (0, R.jsx)("span", {
					className: "rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500",
					children: "vai trò gán được"
				}) : /* @__PURE__ */ (0, R.jsx)("span", {
					className: "rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700",
					children: "vai trò tương thích cũ"
				}),
				/* @__PURE__ */ (0, R.jsxs)("span", {
					className: "ml-auto text-[11.5px] font-bold text-slate-400",
					children: [e.permissionCount, " quyền"]
				})
			]
		}), /* @__PURE__ */ (0, R.jsx)("div", {
			className: "mt-2 flex flex-wrap gap-1.5",
			"data-testid": "user-access-role-permissions",
			children: e.wildcard ? /* @__PURE__ */ (0, R.jsx)("span", {
				className: "break-words text-[12.5px] leading-relaxed text-slate-500",
				children: "Toàn quyền trên mọi thao tác của hệ thống (dấu * trong ma trận nguyên bản của core.auth)."
			}) : e.permissions.map((e) => /* @__PURE__ */ (0, R.jsx)(Bc, { name: e }, e))
		})]
	});
}
function qc() {
	return /* @__PURE__ */ (0, R.jsx)("div", {
		"data-testid": "user-access-empty",
		className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] leading-relaxed text-slate-600",
		children: "Nguồn tài khoản của bản dựng này chưa có người dùng nào (hoặc chưa cấu hình). Trang hiển thị đúng trạng thái trống và không tự bịa tài khoản, vai trò hay quyền nào thay thế."
	});
}
function Jc() {
	let e = T(), { toast: t } = Jn(), n = (0, _.useSyncExternalStore)(C, S, S), r = (0, _.useMemo)(() => (n?.lastWrites ?? []).filter((e) => e.event === "user_create" || e.event === "user_role_set" || e.event === "user_active_set" || e.event === "user_password_reset"), [n]), { assignableSet: i, activeCount: a } = (0, _.useMemo)(() => ({
		assignableSet: new Set(e?.roles.assignable ?? []),
		activeCount: (e?.users ?? []).filter((e) => e.active).length
	}), [e]), [o, s] = (0, _.useState)(!1), [c, l] = (0, _.useState)(null), [u, d] = (0, _.useState)(null), [f, p] = (0, _.useState)(null);
	if (!e) return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "max-w-[1240px] pb-3",
		children: /* @__PURE__ */ (0, R.jsx)("div", {
			className: "rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 px-4 py-5 text-[14px] text-slate-600",
			children: "Chưa có dữ liệu người dùng & phân quyền từ máy chủ. Trang chỉ đọc và không tự tạo dữ liệu thay thế."
		})
	});
	let m = e.canManage === !0, h = e.roles.assignable, g = r;
	return /* @__PURE__ */ (0, R.jsxs)("div", {
		className: "max-w-[1240px] space-y-4 pb-3",
		children: [
			/* @__PURE__ */ (0, R.jsxs)("section", {
				className: "rounded-2xl border border-slate-200 bg-white p-4 md:p-5",
				"data-testid": "user-access-header",
				children: [
					/* @__PURE__ */ (0, R.jsx)(J, {
						icon: /* @__PURE__ */ (0, R.jsx)(to, { size: 20 }),
						title: "Người dùng & Vai trò",
						sub: m ? "Quản lý tài khoản, vai trò và trạng thái hoạt động — đúng vai trò gán được của hệ thống, không thêm vai trò mới, không hiện dữ liệu bí mật." : "Xem tài khoản, vai trò và ma trận phân quyền đúng như hệ thống đang dùng — không thêm vai trò mới, không hiện dữ liệu bí mật.",
						right: m ? /* @__PURE__ */ (0, R.jsxs)(wo, {
							onClick: () => s(!0),
							className: "min-h-[40px] px-4 text-[13.5px]",
							children: [/* @__PURE__ */ (0, R.jsx)($a, { size: 16 }), " + THÊM TÀI KHOẢN"]
						}) : /* @__PURE__ */ (0, R.jsx)(q, {
							tone: "blue",
							size: "sm",
							children: "CHỈ ĐỌC"
						})
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "mt-3 flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-slate-600",
						children: [
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "rounded-lg bg-slate-100 px-2 py-1",
								"data-testid": "user-access-authmode",
								children: e.authMode.label
							}),
							/* @__PURE__ */ (0, R.jsx)("span", {
								className: "rounded-lg bg-slate-100 px-2 py-1",
								"data-testid": "user-access-counts",
								children: e.counts.userShown === e.counts.userCount ? `${e.counts.userCount} tài khoản` : `${e.counts.userShown}/${e.counts.userCount} tài khoản (giới hạn hiển thị)`
							}),
							/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "rounded-lg bg-slate-100 px-2 py-1",
								children: [
									a,
									" hoạt động · ",
									e.counts.inactiveCount,
									" vô hiệu hóa"
								]
							}),
							/* @__PURE__ */ (0, R.jsxs)("span", {
								className: "rounded-lg bg-slate-100 px-2 py-1",
								children: [e.counts.roleCount, " vai trò trong ma trận"]
							}),
							!m && /* @__PURE__ */ (0, R.jsxs)("span", {
								className: "inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 text-emerald-800",
								children: [/* @__PURE__ */ (0, R.jsx)(ka, { size: 13 }), " không sửa từ trang này"]
							})
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("p", {
						"data-testid": "user-access-mode-note",
						className: U("mt-3 rounded-xl px-3 py-2.5 text-[13px] leading-relaxed", e.authMode.required ? "border border-blue-200 bg-blue-50 text-blue-900" : "border border-amber-200 bg-amber-50 text-amber-900"),
						children: [
							/* @__PURE__ */ (0, R.jsxs)("b", { children: [
								"Chế độ xác thực: ",
								e.authMode.label,
								"."
							] }),
							" ",
							e.authMode.note
						]
					}),
					/* @__PURE__ */ (0, R.jsxs)("div", {
						"data-testid": "user-access-current",
						className: "mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5",
						children: [/* @__PURE__ */ (0, R.jsx)(Xr, {
							size: 22,
							className: "shrink-0 text-[#1e5aa8]"
						}), /* @__PURE__ */ (0, R.jsxs)("div", {
							className: "min-w-0",
							children: [/* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
								children: "Bạn đang đăng nhập"
							}), e.currentUser.present ? /* @__PURE__ */ (0, R.jsxs)("p", {
								className: "min-w-0 break-words text-[14px] font-extrabold text-[#0f2a4a]",
								children: [
									e.currentUser.displayName,
									" ",
									/* @__PURE__ */ (0, R.jsxs)("span", {
										className: "font-mono text-[12px] font-semibold text-slate-500",
										children: [
											"(",
											e.currentUser.username,
											")"
										]
									}),
									" ",
									"· ",
									Ic(e.currentUser.role),
									e.currentUser.wildcard ? " · toàn quyền (*)" : ` · ${e.currentUser.permissions.length} quyền`
								]
							}) : /* @__PURE__ */ (0, R.jsx)("p", {
								className: "text-[14px] font-bold text-slate-500",
								children: "Chưa xác định phiên đăng nhập"
							})]
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, R.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-[1fr_340px]",
				children: [/* @__PURE__ */ (0, R.jsxs)("div", {
					className: "min-w-0 space-y-4",
					children: [/* @__PURE__ */ (0, R.jsxs)("section", {
						className: "space-y-2.5",
						"data-testid": "user-access-accounts",
						children: [/* @__PURE__ */ (0, R.jsx)(J, {
							icon: /* @__PURE__ */ (0, R.jsx)(Za, { size: 18 }),
							title: "Tài khoản",
							sub: "Trường công khai chuẩn của tài khoản (tên hiển thị, tài khoản đăng nhập, vai trò, trạng thái). Không có mật khẩu hay hash."
						}), e.users.length === 0 ? /* @__PURE__ */ (0, R.jsx)(qc, {}) : e.users.map((e) => /* @__PURE__ */ (0, R.jsx)(Gc, {
							account: e,
							canManage: m,
							onManageRole: () => l(e),
							onManageActive: () => d(e),
							onManagePassword: () => p(e)
						}, e.user_id || e.username))]
					}), /* @__PURE__ */ (0, R.jsxs)("section", {
						className: "space-y-2.5",
						"data-testid": "user-access-matrix",
						children: [
							/* @__PURE__ */ (0, R.jsx)(J, {
								icon: /* @__PURE__ */ (0, R.jsx)(Mi, { size: 18 }),
								title: "Ma trận phân quyền",
								sub: "Nguyên văn ROLE_PERMISSIONS của core.auth — nguồn quyền duy nhất của ứng dụng. Tên quyền giữ nguyên bản, không dịch, không thêm."
							}),
							e.permissionMatrix.map((e) => /* @__PURE__ */ (0, R.jsx)(Kc, {
								row: e,
								assignable: i.has(e.role)
							}, e.role)),
							/* @__PURE__ */ (0, R.jsxs)("p", {
								className: "break-words text-[12px] leading-relaxed text-slate-400",
								children: [
									"Nguồn: ",
									e.roles.source,
									". Vai trò gán được cho tài khoản:",
									" ",
									e.roles.assignable.map((e) => Ic(e)).join(", "),
									".",
									e.roles.legacy.length > 0 ? ` Các vai trò còn lại (${e.roles.legacy.map((e) => Ic(e)).join(", ")}) chỉ còn trong ma trận để tương thích dữ liệu cũ.` : ""
								]
							})
						]
					})]
				}), /* @__PURE__ */ (0, R.jsxs)("aside", {
					className: "min-w-0 space-y-3",
					children: [/* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
						children: [/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, R.jsx)(Ai, { size: 14 }), " Trang này không có"]
						}), /* @__PURE__ */ (0, R.jsx)("ul", {
							className: "mt-1 space-y-1 text-[12.5px] leading-relaxed text-slate-600",
							"data-testid": "user-access-unavailable",
							children: e.unavailable.map((e) => /* @__PURE__ */ (0, R.jsx)("li", {
								className: "break-words",
								children: e
							}, e))
						})]
					}), /* @__PURE__ */ (0, R.jsxs)("div", {
						className: "rounded-xl border border-slate-200 bg-white px-3 py-2.5",
						children: [/* @__PURE__ */ (0, R.jsxs)("p", {
							className: "flex items-center gap-1.5 text-[12px] font-extrabold uppercase tracking-wide text-slate-500",
							children: [/* @__PURE__ */ (0, R.jsx)(ka, { size: 14 }), " Quyền của bạn được kiểm ở đâu"]
						}), /* @__PURE__ */ (0, R.jsxs)("p", {
							className: "mt-1 text-[12.5px] leading-relaxed text-slate-600",
							children: [
								"Mọi thao tác ghi trong ứng dụng vẫn được kiểm tra bởi",
								/* @__PURE__ */ (0, R.jsx)("span", {
									className: "font-mono text-[11.5px] font-semibold",
									children: " core.auth "
								}),
								"trên máy chủ theo đúng ma trận trên. Trang này chỉ hiển thị quy tắc, không tự nới quyền."
							]
						})]
					})]
				})]
			}),
			m && o && /* @__PURE__ */ (0, R.jsx)(Vc, {
				assignableRoles: h,
				onClose: () => s(!1),
				lastWrites: g,
				onSuccess: (e) => {
					s(!1), t("Đã tạo tài khoản " + e, "Ghi qua core.database.save_user, có audit.", "green");
				}
			}),
			m && c && /* @__PURE__ */ (0, R.jsx)(Hc, {
				account: c,
				assignableRoles: h,
				onClose: () => l(null),
				lastWrites: g,
				onSuccess: () => {
					let e = c.display_name || c.username;
					l(null), t("Đã đổi vai trò " + e, "Vai trò mới có hiệu lực từ dữ liệu mới nhất.", "green");
				}
			}),
			m && u && /* @__PURE__ */ (0, R.jsx)(Uc, {
				account: u,
				onClose: () => d(null),
				lastWrites: g,
				onSuccess: () => {
					let e = u.display_name || u.username, n = !u.active;
					d(null), t((n ? "Đã kích hoạt lại " : "Đã vô hiệu hóa ") + e, "Trạng thái mới có hiệu lực từ dữ liệu mới nhất.", "green");
				}
			}),
			m && f && /* @__PURE__ */ (0, R.jsx)(Wc, {
				account: f,
				onClose: () => p(null),
				lastWrites: g,
				onSuccess: () => {
					let e = f.display_name || f.username;
					p(null), t("Đã đặt mật khẩu mới cho " + e, "Mật khẩu cũ không còn dùng được.", "green");
				}
			})
		]
	});
}
//#endregion
//#region src/pages/NotFound.tsx
function Yc() {
	return /* @__PURE__ */ (0, R.jsxs)("section", {
		className: "rounded-2xl bg-white border border-slate-200 p-6",
		"data-testid": "not-found",
		children: [/* @__PURE__ */ (0, R.jsx)("h1", {
			className: "text-xl font-bold",
			children: "Không tìm thấy màn hình / đường dẫn không hợp lệ"
		}), /* @__PURE__ */ (0, R.jsxs)("nav", {
			className: "flex flex-wrap gap-4 mt-4",
			children: [
				/* @__PURE__ */ (0, R.jsx)(L, {
					to: "/",
					children: "Tổng Quan"
				}),
				/* @__PURE__ */ (0, R.jsx)(L, {
					to: "/hop-dong",
					children: "Hợp đồng"
				}),
				/* @__PURE__ */ (0, R.jsx)(L, {
					to: "/lo-hang",
					children: "Lô Hàng"
				})
			]
		})]
	});
}
//#endregion
//#region src/App.tsx
function Xc() {
	return /* @__PURE__ */ (0, R.jsx)("div", {
		className: "min-h-[40vh] grid place-items-center",
		children: /* @__PURE__ */ (0, R.jsx)("p", {
			className: "text-[15px] font-semibold text-slate-500",
			children: "Đang tải dữ liệu vận hành…"
		})
	});
}
function Zc() {
	let e = (0, _.useSyncExternalStore)(C, S, S);
	return /* @__PURE__ */ (0, R.jsx)(qn, { children: /* @__PURE__ */ (0, R.jsx)(Ut, { children: /* @__PURE__ */ (0, R.jsx)(Po, { children: e ? /* @__PURE__ */ (0, R.jsxs)(Kt, { children: [
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/",
			element: /* @__PURE__ */ (0, R.jsx)(Lo, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/viec-can-xu-ly",
			element: /* @__PURE__ */ (0, R.jsx)(Vo, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/lo-hang",
			element: /* @__PURE__ */ (0, R.jsx)(Yo, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/lo-hang/:id",
			element: /* @__PURE__ */ (0, R.jsx)(hs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/tao-lo-moi",
			element: /* @__PURE__ */ (0, R.jsx)(gs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/theo-doi",
			element: /* @__PURE__ */ (0, R.jsx)(_s, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/khach-hang",
			element: /* @__PURE__ */ (0, R.jsx)(Ss, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/tai-chinh/thu-tien",
			element: /* @__PURE__ */ (0, R.jsx)(vs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/tai-chinh/cong-no-doi-tac",
			element: /* @__PURE__ */ (0, R.jsx)(bs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/kinh-doanh-bao-gia",
			element: /* @__PURE__ */ (0, R.jsx)(js, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/thoa-thuan-ban-giao",
			element: /* @__PURE__ */ (0, R.jsx)(Is, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/hop-dong",
			element: /* @__PURE__ */ (0, R.jsx)(Ls, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/hop-dong/moi",
			element: /* @__PURE__ */ (0, R.jsx)(Ws, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/hop-dong/:id",
			element: /* @__PURE__ */ (0, R.jsx)(Hs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/tra-cuu-thue",
			element: /* @__PURE__ */ (0, R.jsx)(qs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/dich-thuat",
			element: /* @__PURE__ */ (0, R.jsx)(Qs, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/ngu-canh-doi-tac",
			element: /* @__PURE__ */ (0, R.jsx)(oc, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/tai-chinh/doi-soat",
			element: /* @__PURE__ */ (0, R.jsx)(vc, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/bao-cao-ceo",
			element: /* @__PURE__ */ (0, R.jsx)(Dc, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/so-tay",
			element: /* @__PURE__ */ (0, R.jsx)(Fc, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "/nguoi-dung",
			element: /* @__PURE__ */ (0, R.jsx)(Jc, {})
		}),
		/* @__PURE__ */ (0, R.jsx)(Wt, {
			path: "*",
			element: /* @__PURE__ */ (0, R.jsx)(Yc, {})
		})
	] }) : /* @__PURE__ */ (0, R.jsx)(Xc, {}) }) }) });
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/typeof.js
function Qc(e) {
	"@babel/helpers - typeof";
	return Qc = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, Qc(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPrimitive.js
function $c(e, t) {
	if (Qc(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (Qc(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/toPropertyKey.js
function el(e) {
	var t = $c(e, "string");
	return Qc(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.148.0/helpers/esm/defineProperty.js
function tl(e, t, n) {
	return (t = el(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region src/component-entry.tsx
var nl = class extends _.Component {
	constructor(...e) {
		super(...e), tl(this, "state", { error: null });
	}
	static getDerivedStateFromError(e) {
		return { error: e };
	}
	render() {
		return this.state.error ? /* @__PURE__ */ (0, R.jsx)("div", {
			style: {
				padding: 24,
				fontFamily: "inherit"
			},
			children: /* @__PURE__ */ (0, R.jsxs)("div", {
				style: {
					border: "2px solid #fca5a5",
					background: "#fef2f2",
					borderRadius: 16,
					padding: 20,
					textAlign: "center",
					color: "#991b1b"
				},
				children: [/* @__PURE__ */ (0, R.jsx)("p", {
					style: {
						fontWeight: 800,
						fontSize: 16,
						margin: 0
					},
					children: "Logi-good shell gặp lỗi khi render"
				}), /* @__PURE__ */ (0, R.jsxs)("p", {
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
}, rl = null, il = null;
function al(e) {
	return il && e.contains(il) ? il : (il = document.createElement("div"), il.className = "logi-shell", e.appendChild(il), il);
}
function ol(e) {
	k(e.setTriggerValue ?? null);
	let t = al(e.parentElement);
	return rl || (rl = (0, v.createRoot)(t), rl.render(/* @__PURE__ */ (0, R.jsx)(nl, { children: /* @__PURE__ */ (0, R.jsx)(Zc, {}) }))), e.data && typeof e.data == "object" && x(e.data), () => {
		try {
			rl?.unmount();
		} catch {}
		rl = null;
		try {
			il?.remove();
		} catch {}
		il = null, k(null);
	};
}
//#endregion
export { ol as default };
