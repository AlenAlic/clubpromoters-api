# Flask Vue Boilerplate

## Starting a new project from this boilerplate
1. Download this project from GitHub.
2. Create a new GitHub repository for the project.
3. Install the base dependencies (`pip install -r requirements.txt` and `npm install`).
4. Copy the `/public/config/development.json.example` to `/public/config/development.json` and customize it as desired.



## Project setup 
### Compiles and hot-reloads frontend for development
`npm run serve`

This exposes the frontend on `http://127.0.0.1:8080`.

### Lints and fixes files
`npm run lint`

### Runs the backend in debug mode.
`python run.py`

This exposes the backend on `http://127.0.0.1:4040`.


## Tweaks
### Remove references to boilerplate
- Change the name in `package.json` and `package-lock.json`.
- Change the `TOKEN_PREFIX` constant in `/src/api/util/token-storage.js`.
- Change any references in `/public/index.html`.
- Change any references in `/public/manifest.json`.
