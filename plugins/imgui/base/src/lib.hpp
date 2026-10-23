#pragma once
// Glue between the Dear ImGui backend and an exlaunch base that uses OdysseyHeaders
// (nn::Result is the vapours class there, while exlaunch's own results are plain integers).
#include "nn/types.h"
#include "lib/diag/assert.hpp"
#include "lib/result.hpp"

namespace odn {
inline bool failed(unsigned int r) { return r != 0; }
template <typename T> inline bool failed(const T &r) { return r.IsFailure(); }
}
// Brace form on purpose: the helpers call it with or without a trailing ';'.
#undef R_ABORT_UNLESS
#define R_ABORT_UNLESS(expr) { const auto _odn_r = (expr); if (::odn::failed(_odn_r)) { __builtin_trap(); } }
