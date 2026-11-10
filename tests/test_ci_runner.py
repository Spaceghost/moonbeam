#!/usr/bin/env python3
"""Admission cannot be widened by a dispatch input or a fork."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('ci_runner', Path(__file__).resolve().parents[1] / 'scripts/ci-runner.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
owner = dict(GITHUB_REPOSITORY='Spaceghost/moonbeam', GITHUB_ACTOR='Spaceghost',
             GITHUB_TRIGGERING_ACTOR='Spaceghost', GITHUB_EVENT_NAME='push', SELF_HOSTED_ENABLED='true')
assert 'self-hosted' in module.select(owner)
assert module.select(dict(owner, RUNNER_MODE='github')) == ['ubuntu-22.04']
assert module.select(dict(owner, SELF_HOSTED_ENABLED='false')) == ['ubuntu-22.04']
for change in [dict(GITHUB_REPOSITORY='outsider/moonbeam'), dict(GITHUB_ACTOR='outsider'),
               dict(GITHUB_TRIGGERING_ACTOR='outsider'), dict(GITHUB_EVENT_NAME='pull_request'),
               dict(GITHUB_EVENT_NAME='pull_request_target')]:
    env = dict(owner, **change)
    assert module.select(env) == ['ubuntu-22.04']
    try:
        module.select(dict(env, RUNNER_MODE='self-hosted'))
    except ValueError:
        pass
    else:
        raise AssertionError(change)
print('PASS: hybrid routing, hosted override, disabled capacity, repository/actor/fork admission')
