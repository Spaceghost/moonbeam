#pragma once
#include <Limelight.h>

namespace ReconnectPolicy {
inline bool canRetryTermination(int errorCode)
{
    return errorCode != ML_ERROR_GRACEFUL_TERMINATION &&
           errorCode != ML_ERROR_PROTECTED_CONTENT &&
           errorCode != ML_ERROR_FRAME_CONVERSION &&
           errorCode != ML_ERROR_UNEXPECTED_EARLY_TERMINATION;
}
}
