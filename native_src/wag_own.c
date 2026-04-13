#include <jni.h>
#include <android/log.h>
#include <stdlib.h>
#include <string.h>

#define TAG "libwag_own"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

__attribute__((constructor))
static void on_load(void) {
    LOGI("libwag_own loaded - Mobile Spoof Bypass v2");
    setenv("ro.product.model",        "SM-A546E",  1);
    setenv("ro.product.brand",        "samsung",   1);
    setenv("ro.product.manufacturer", "samsung",   1);
    setenv("ro.product.name",         "a54xnsxx",  1);
    setenv("ro.product.device",       "a54x",      1);
    setenv("ro.build.fingerprint",
        "samsung/a54xnsxx/a54x:13/TP1A.220624.014/A546EXXS5EXL1:user/release-keys", 1);
    LOGI("Device spoofed as SM-A546E");
}
