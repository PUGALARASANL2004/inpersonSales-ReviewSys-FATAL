module.exports = {
  apps: [
    {
      name: 'api',
      script: '.venv/bin/python',
      args: '-m uvicorn api.main:app --host 0.0.0.0 --port 8000',
      cwd: '/home/ec2-user/inpersonSales-ReviewSys',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      log_file: './logs/api-combined.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      merge_logs: true,
      // Restart on file changes (optional, set to false in production)
      ignore_watch: ['node_modules', 'logs', '.git'],
    },
    {
      name: 'ui',
      // Using npx serve (no global install needed)
      script: 'npx',
      args: 'serve -s ui/build -l 3000',
      cwd: '/home/ec2-user/inpersonSales-ReviewSys',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      error_file: './logs/ui-error.log',
      out_file: './logs/ui-out.log',
      log_file: './logs/ui-combined.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      merge_logs: true,
    },
  ],
};

