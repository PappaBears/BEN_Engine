// Minimal Unity-compatible shim used ONLY by the host Makefile fallback when the
// PlatformIO `native` platform (and its bundled Unity) cannot be downloaded.
// `pio test -e native` uses the real ThrowTheSwitch Unity instead; the test sources are
// written against the subset of the Unity API implemented here.
#pragma once
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cstdlib>

extern "C" void setUp(void);
extern "C" void tearDown(void);

namespace unity_shim {
inline int tests = 0, failures = 0, ignored = 0;
inline bool current_failed = false;
inline const char* current_name = "";
inline void fail(const char* file, int line, const char* msg) {
    if (!current_failed) { ++failures; current_failed = true; }
    printf("%s:%d:%s:FAIL: %s\n", file, line, current_name, msg);
}
}

#define UNITY_BEGIN() (unity_shim::tests = unity_shim::failures = unity_shim::ignored = 0, 0)
#define UNITY_END() (printf("\n-----------------------\n%d Tests %d Failures %d Ignored\n%s\n", \
    unity_shim::tests, unity_shim::failures, unity_shim::ignored, unity_shim::failures ? "FAIL" : "OK"), unity_shim::failures)
#define RUN_TEST(fn) do { unity_shim::current_name = #fn; unity_shim::current_failed = false; ++unity_shim::tests; \
    setUp(); fn(); tearDown(); if (!unity_shim::current_failed) printf("%s:%d:%s:PASS\n", __FILE__, __LINE__, #fn); } while (0)

#define UNITY_FAIL_(msg) unity_shim::fail(__FILE__, __LINE__, msg)
#define TEST_FAIL_MESSAGE(msg) UNITY_FAIL_(msg)
#define TEST_ASSERT(c) do { if (!(c)) UNITY_FAIL_("Expression evaluated to FALSE: " #c); } while (0)
#define TEST_ASSERT_TRUE(c) TEST_ASSERT(c)
#define TEST_ASSERT_FALSE(c) do { if ((c)) UNITY_FAIL_("Expression evaluated to TRUE: " #c); } while (0)
#define TEST_ASSERT_TRUE_MESSAGE(c, m) do { if (!(c)) UNITY_FAIL_(m); } while (0)
#define TEST_ASSERT_FALSE_MESSAGE(c, m) do { if ((c)) UNITY_FAIL_(m); } while (0)
#define TEST_ASSERT_NULL(p) TEST_ASSERT((p) == nullptr)
#define TEST_ASSERT_NOT_NULL(p) TEST_ASSERT((p) != nullptr)
#define TEST_ASSERT_EQUAL(e, a) do { long long _e = (long long)(e), _a = (long long)(a); if (_e != _a) { char _b[160]; \
    snprintf(_b, sizeof _b, "Expected %lld Was %lld (%s)", _e, _a, #a); UNITY_FAIL_(_b); } } while (0)
#define TEST_ASSERT_EQUAL_INT(e, a) TEST_ASSERT_EQUAL(e, a)
#define TEST_ASSERT_EQUAL_INT32(e, a) TEST_ASSERT_EQUAL(e, a)
#define TEST_ASSERT_EQUAL_UINT32(e, a) TEST_ASSERT_EQUAL(e, a)
#define TEST_ASSERT_EQUAL_UINT(e, a) TEST_ASSERT_EQUAL(e, a)
#define TEST_ASSERT_EQUAL_size_t(e, a) TEST_ASSERT_EQUAL(e, a)
#define TEST_ASSERT_EQUAL_STRING(e, a) do { const char* _e = (e); const char* _a = (a); \
    if (!_e || !_a || strcmp(_e, _a) != 0) { char _b[1200]; snprintf(_b, sizeof _b, "Expected '%s' Was '%s'", _e ? _e : "(null)", _a ? _a : "(null)"); UNITY_FAIL_(_b); } } while (0)
#define TEST_ASSERT_EQUAL_FLOAT(e, a) do { double _e = (e), _a = (a); if (std::fabs(_e - _a) > std::fabs(_e) * 1e-5 + 1e-5) { \
    char _b[160]; snprintf(_b, sizeof _b, "Expected %g Was %g", _e, _a); UNITY_FAIL_(_b); } } while (0)
#define TEST_ASSERT_FLOAT_WITHIN(d, e, a) do { double _e = (e), _a = (a); if (std::fabs(_e - _a) > (d)) { \
    char _b[160]; snprintf(_b, sizeof _b, "Expected %g +/- %g Was %g", _e, (double)(d), _a); UNITY_FAIL_(_b); } } while (0)
#define TEST_ASSERT_DOUBLE_WITHIN(d, e, a) TEST_ASSERT_FLOAT_WITHIN(d, e, a)
#define TEST_ASSERT_GREATER_THAN(t, a) TEST_ASSERT((a) > (t))
#define TEST_ASSERT_LESS_THAN(t, a) TEST_ASSERT((a) < (t))
#define TEST_ASSERT_GREATER_OR_EQUAL(t, a) TEST_ASSERT((a) >= (t))
#define TEST_IGNORE() do { ++unity_shim::ignored; return; } while (0)
