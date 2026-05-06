#pragma once

#include "venus_entity.hh"
#include <memory>
#include <utility>
#include <vector>
class VenusAlgorithm {
public:
  typedef std::pair<int, int> Coordinate;

  struct CoordinateDescriptor {
    Coordinate coords;
    Entity entity;
  };

  Entity *getEntityAtCoordinate(const Coordinate &coords) noexcept;
  int placeEntityAtCoordinate(const Coordinate &coords,
                              std::unique_ptr<Entity>) noexcept;

  int isEntityAtCoordinate(const Coordinate &coords) noexcept;

  int algorithmLoop();
  

  VenusAlgorithm();
  ~VenusAlgorithm();

private:
  std::vector<std::vector<int>>
      map_; // integer map to indicate object existence at specific coordinates
  std::vector<CoordinateDescriptor>
      entityMap_; // vector of coordinate descriptors to query for entities at
                  // specific coordinates
};