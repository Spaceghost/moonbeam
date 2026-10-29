#pragma once
#include <cstdint>

namespace AudioQueueBudget {
// Bound duration in bytes, including partial packets and the incoming packet.
inline bool fits(std::uint64_t queued, std::uint64_t incoming, std::uint64_t bytesPerSecond)
{
    const auto limit = bytesPerSecond * 50 / 1000;
    return bytesPerSecond != 0 && incoming <= limit && queued <= limit - incoming;
}
}
