const CopyPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlInlineScriptPlugin = require('html-inline-script-webpack-plugin');
const LicensePlugin = require('webpack-license-plugin')
const TerserPlugin = require('terser-webpack-plugin');

const path = require('path');

module.exports = {
  mode: 'production',
  entry: './src/index.js',
  optimization: {
    minimizer: [new TerserPlugin({
      extractComments: false,
    })],
  },
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'dist'),
  },
  plugins: [
    new CopyPlugin({
      patterns: [{
          from: './umringpolygon-zu-xplanung.model3',
          to: 'umringpolygon-zu-xplanung.model3'
        },
        {
          from: './LICENSE',
          to: 'umringpolygon-zu-xplanung_license.txt'
        }
      ],
    }),
    new HtmlWebpackPlugin({
      append: true,
      template: path.join(__dirname, 'src/index.html')
    }),
    new HtmlInlineScriptPlugin(),
    new LicensePlugin({
      // Add license text for isarray
      excludedPackageTest: name => name === 'isarray',
      additionalFiles: {
        'oss-licenses.json': packages => JSON.stringify([...packages, {
          'name': 'isarray',
          'version': '1.0.0',
          "author": "Julian Gruber <mail@juliangruber.com> (http://juliangruber.com)",
          "repository": "https://github.com/juliangruber/isarray",
          "license": "MIT",
          "licenseText": "MIT License\n\nCopyright (c) 2013 Julian Gruber <julian@juliangruber.com>\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n"
        }], null, 2)
      }
    })
  ]
};