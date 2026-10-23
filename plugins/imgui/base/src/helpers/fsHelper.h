#pragma once

#include "lib.hpp"
#include "nn/fs.h"

namespace FsHelper {

    struct LoadData {
        const char *path;
        void *buffer;
        long bufSize;
    };

    bool writeFileToPath(void *buf, size_t size, const char *path);

    void loadFileFromPath(LoadData &loadData);

    long getFileSize(const char *path);

    bool isFileExist(const char *path);
}
