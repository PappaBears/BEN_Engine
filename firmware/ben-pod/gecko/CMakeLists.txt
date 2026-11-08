# BEN Engine — BEN Pod v1 — CMake build for the Silicon Labs flow (Schreiber AI)
#
# Usage (after `slc generate -p ben_pod.slcp -d build/gen -o cmake --with mgm240pb32vna`):
#   cmake -S gecko -B gecko/build -G Ninja -DCMAKE_TOOLCHAIN_FILE=$BEN_SISDK/cmake/toolchain.cmake \
#         -DBEN_SISDK=$BEN_SISDK -DSLC_GEN_DIR=gecko/build/gen
#   cmake --build gecko/build
#   commander gbl create ben_pod.gbl --app gecko/build/ben_pod.s37 --sign ben-pod-signing-key.pem   (signed OTA image)
#
# The SLC generator emits a `ben_pod.cmake` with every SDK source/include/define the components need;
# this file pulls it in and adds the BEN application. Nothing here compiles on a host without the SDK.
# STATUS: NOT compiled on the build host (no toolchain). See firmware/README.md.
cmake_minimum_required(VERSION 3.21)
project(ben_pod C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)

set(BEN_SISDK "$ENV{BEN_SISDK}" CACHE PATH "Simplicity SDK root")
set(SLC_GEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/build/gen" CACHE PATH "Output of slc generate -o cmake")
option(BEN_POD_W_BATTERY "Build the sleepy (MTD) battery Pod W variant" OFF)
set(BEN_FW_VERSION "1.0.0" CACHE STRING "Firmware version string reported in status.fw")
set(BEN_RING_SECONDS 3600 CACHE STRING "Telemetry ring buffer depth in seconds (1 Hz)")

if(NOT EXISTS "${SLC_GEN_DIR}/ben_pod.cmake")
  message(FATAL_ERROR "Run slc generate first (see header). Missing ${SLC_GEN_DIR}/ben_pod.cmake")
endif()
include("${SLC_GEN_DIR}/ben_pod.cmake")    # defines target slc_ben_pod with SDK sources, includes, defines

set(BEN_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/..")
add_library(bencore STATIC
  ${BEN_ROOT}/lib/bencore/alarms.cpp
  ${BEN_ROOT}/lib/bencore/channels.cpp
  ${BEN_ROOT}/lib/bencore/commands.cpp
  ${BEN_ROOT}/lib/bencore/node_app.cpp
  ${BEN_ROOT}/lib/bencore/outputs.cpp
  ${BEN_ROOT}/lib/bencore/ringbuf.cpp
  ${BEN_ROOT}/lib/bencore/telemetry.cpp
  ${BEN_ROOT}/lib/bencore/timesync.cpp)
target_include_directories(bencore PUBLIC ${BEN_ROOT}/lib ${BEN_ROOT}/lib/bencore ${BEN_ROOT}/lib/benhal)
target_compile_definitions(bencore PUBLIC BEN_FW_VERSION="${BEN_FW_VERSION}" BEN_RING_SECONDS=${BEN_RING_SECONDS})
target_compile_options(bencore PRIVATE -Wall -Wextra -Wno-unused-parameter -fno-exceptions -fno-rtti)

add_executable(ben_pod
  ${BEN_ROOT}/src/main.cpp
  ${BEN_ROOT}/lib/benhal/hal_efr32.cpp)
target_compile_definitions(ben_pod PRIVATE BEN_TARGET_EFR32 MBEDTLS_USE_PSA_CRYPTO)
if(BEN_POD_W_BATTERY)
  target_compile_definitions(ben_pod PRIVATE BEN_POD_W_BATTERY)
endif()
target_link_libraries(ben_pod PRIVATE bencore slc_ben_pod)
target_link_options(ben_pod PRIVATE
  -T${SLC_GEN_DIR}/autogen/linkerfile.ld
  -Wl,--gc-sections -Wl,-Map=ben_pod.map
  --specs=nano.specs --specs=nosys.specs)
set_target_properties(ben_pod PROPERTIES OUTPUT_NAME ben_pod SUFFIX .axf)

# s37 / bin / size for commander and the release manifest
add_custom_command(TARGET ben_pod POST_BUILD
  COMMAND ${CMAKE_OBJCOPY} -O srec $<TARGET_FILE:ben_pod> ben_pod.s37
  COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:ben_pod> ben_pod.bin
  COMMAND ${CMAKE_SIZE} $<TARGET_FILE:ben_pod>
  COMMENT "s37/bin for commander gbl create (sign with the HSM-held ECDSA P-256 key, see firmware/README.md)")
