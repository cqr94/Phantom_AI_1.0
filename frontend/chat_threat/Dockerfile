# Use the official lightweight Node.js 20 image
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (if available) first
# This allows Docker to cache your npm install layer efficiently
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your frontend application files
COPY . .

# Expose the port Vite runs on
EXPOSE 5173

# Start the Vite development server with the --host flag
# This is crucial so Docker can route traffic from your Mac to the container
CMD ["npm", "run", "dev", "--", "--host"]