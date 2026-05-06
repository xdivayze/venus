cmake_minimum_required(VERSION 3.16)
project(venus_algorithm)
add_library(venus_algorithm)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

target_sources(venus_algorithm PRIVATE src/venus_alg.cc)
target_include_directories(venus_algorithm PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
