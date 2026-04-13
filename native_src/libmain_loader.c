#include <dlfcn.h>
#include <android/log.h>
#include <stdlib.h>

#define TAG             "libmain_loader"
#define WAG_LIB_PATH    "/data/local/tmp/libwag_own.so"
#define BACKUP_LIB_PATH "/data/local/tmp/libmain_backup.so"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

__attribute__((constructor))
static void loader_init(void) {
    LOGI("libmain_loader initializing...");
    void* wag = dlopen(WAG_LIB_PATH, RTLD_NOW | RTLD_GLOBAL);
    if (!wag) {
        LOGI("ERROR loading libwag_own: %s", dlerror());
    } else {
        LOGI("libwag_own loaded OK");
    }
    void* orig = dlopen(BACKUP_LIB_PATH, RTLD_NOW | RTLD_GLOBAL);
    if (!orig) {
        LOGI("ERROR loading backup: %s", dlerror());
    } else {
        LOGI("libmain backup loaded OK");
    }
}
