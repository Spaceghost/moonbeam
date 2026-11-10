#!/usr/bin/env python3
"""Select an admitted Linux worker; public/fork actors always use GitHub."""
import json
import os


def select(env):
    mode = env.get('RUNNER_MODE', 'auto') or 'auto'
    if mode not in ('auto', 'github', 'self-hosted'):
        raise ValueError('Unknown runner mode')
    admitted = (env.get('GITHUB_REPOSITORY') == 'Spaceghost/moonbeam'
                and env.get('GITHUB_ACTOR', '').lower() == 'spaceghost'
                and env.get('GITHUB_TRIGGERING_ACTOR', '').lower() == 'spaceghost'
                and env.get('GITHUB_EVENT_NAME') in ('push', 'workflow_dispatch', 'schedule'))
    if mode == 'self-hosted' and not admitted:
        raise ValueError('Self-hosted work requires the admitted repository and owner actor')
    if admitted and mode != 'github' and (mode == 'self-hosted' or env.get('SELF_HOSTED_ENABLED') == 'true'):
        return ['self-hosted', 'Linux', 'X64', 'spaceghost-moonbeam', 'fedora-std']
    return ['ubuntu-22.04']


if __name__ == '__main__':
    print('linux=' + json.dumps(select(os.environ)))
