from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from gazebo_rl_environment import GazeboRLGoalEnv

def main():
    # Create the custom RL environment
    env = make_vec_env(lambda: GazeboRLGoalEnv(), n_envs=1)

    # Train the PPO model
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=500000)

    # Save the trained model
    model.save("ppo_gazebo_goal_agent")
    print("Training completed and model saved.")

if __name__ == "__main__":
    main()