from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import Iterable

from serpent.tree.class_decl import ClassDecl
from serpent.tree.type_decl import TypeDecl, ClassType, LikeCurrent, LikeFeature
from serpent.tree.features import BaseMethod, Field, Constant, Feature
from serpent.tree.expr import Expr
from serpent.semantic_checker.analyze_inheritance import FlattenClass
from serpent.errors import CompilerError



