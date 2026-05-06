#pragma once

#include <cstddef>
class Entity {
public:
  enum EntityType {
    CUBE_3,
    CUBE_6,
    CLIFF,
    HILL,
  };

  enum EntityColor {
    RED,
    BLACK,
    BLUE,
    WHITE,
    GREEN,
    NA,
  };

  int getEntityID();

  std::size_t getEdgeLen();
  EntityColor getEntityColor();
  EntityType getEntityType();

  Entity();
  ~Entity();

private:
  int entityID_;
  std::size_t edgeLen_;
  EntityColor entityColor_;
  EntityType entityType_;
};
