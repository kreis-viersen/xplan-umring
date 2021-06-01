const LicensePlugin = require('webpack-license-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlInlineScriptPlugin = require('html-inline-script-webpack-plugin');

const path = require('path');

module.exports = {
  entry: './src/index.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'dist'),
  },
  plugins: [
    new HtmlWebpackPlugin({
       append: true,
       template: path.join(__dirname, 'src/index.html')
     }),
    new HtmlInlineScriptPlugin(),
    new LicensePlugin()
  ]
};
