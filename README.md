yakonfig
========

yet another config management library, or a yak on a fig

yakonfig provides a YAML parser with the following extensions:
 * !runtime
 * !include_yaml
 * !include_func

<pre>
top_level_name_1:
  key1: !runtime argname

  key2: !include_yaml path-to-yaml-file    # can be relative or absolute path

  key3: !include_func module.path.to.func  
  # if func name ends with "yaml", yakonfig parses return value
</pre>

See [tests](src/tests/yakonfig/test_yakonfig.py) for illustrations.
