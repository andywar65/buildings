const path = require('path');

module.exports = {
  entry: './src/photostation_3d.js',
  output: {
    path: path.resolve(__dirname, './static/buildings/js/'),
    filename: 'photostation_3d.js',
  },
};
