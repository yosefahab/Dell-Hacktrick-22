from gym.envs.registration import register

register(
    id='Hacktrick-v0',
    entry_point='hacktrick_ai_py.mdp.hacktrick_env:Hacktrick',
)

