# Run under FreeCADCmd. Dumps the facts the Machine and post-processor pages are written from:
# the common post-processor property schema (name, title, scope, default, help), the Machine
# model's enumerations and dataclass fields. Output: JSON on stdout.
#   ~/FreeCAD/build/bin/FreeCADCmd -c "exec(open('gypsy/facts/machine.py').read())" > gypsy/facts/machine.json
import json, enum, dataclasses, inspect, subprocess, os, sys
out = {}
try:
    import FreeCAD
    out["freecad_version"] = list(FreeCAD.Version())
except Exception as e:
    out["freecad_version"] = str(e)
try:
    from Path.Post.Processor import PostProcessor
    out["common_property_schema"] = PostProcessor.get_common_property_schema()
    out["rotation_strategies"] = list(getattr(PostProcessor, "ROTATION_STRATEGIES", []))
    out["plane_command_default"] = str(getattr(PostProcessor, "PLANE_COMMAND", ""))
except Exception as e:
    out["common_property_schema_error"] = repr(e)
try:
    import Machine.models.machine as mm
    enums, classes = {}, {}
    for name, obj in vars(mm).items():
        if inspect.isclass(obj) and issubclass(obj, enum.Enum) and obj is not enum.Enum:
            enums[name] = [m.value for m in obj]
        elif inspect.isclass(obj) and dataclasses.is_dataclass(obj):
            classes[name] = [{"field": f.name, "type": str(f.type),
                              "default": (None if f.default is dataclasses.MISSING else
                                          (f.default.value if isinstance(f.default, enum.Enum) else f.default))}
                             for f in dataclasses.fields(obj)]
    out["machine_enums"] = enums
    out["machine_dataclasses"] = classes
except Exception as e:
    out["machine_model_error"] = repr(e)
try:
    from Path.Post.Processor import PostProcessorFactory
    import Path.Preferences as P
    out["machine_based_posts"] = sorted(P.allEnabledPostProcessors()) if hasattr(P, "allEnabledPostProcessors") else "n/a"
except Exception as e:
    out["posts_error"] = repr(e)
print(json.dumps(out, indent=1, default=str))
