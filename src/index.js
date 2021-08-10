import FileSaver from 'file-saver';
import JSZip from 'jszip';
const parser = require('fast-xml-parser');
const Parser = require("fast-xml-parser").j2xParser;
const {
  v4: uuidv4
} = require('uuid');
const slugify = require('slugify')

var template = {
  "xplan:XPlanAuszug": [{
    "@": {
      "xmlns:adv": "http://www.adv-online.de/nas",
      "xmlns:gml": "http://www.opengis.net/gml/3.2",
      "xmlns:xlink": "http://www.w3.org/1999/xlink",
      "xmlns:xplan": "http://www.xplanung.de/xplangml/5/2",
      "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
      "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
      "xmlns:wfs": "http://www.opengis.net/wfs/2.0",
      "gml:id": ""
    },
    "gml:boundedBy": [{
      "gml:Envelope": [{
        "@": {
          "srsName": "EPSG:25832"
        },
        "gml:lowerCorner": "",
        "gml:upperCorner": ""
      }]
    }],
    "gml:featureMember": [{
      "xplan:BP_Bereich": [{
        "@": {
          "gml:id": ""
        },
        "xplan:nummer": 0,
        "xplan:name": "Basisplan",
        "xplan:gehoertZuPlan": [{
          "@": {
            "xlink:href": ""
          }
        }]
      }]
    }, {
      "xplan:BP_Plan": [{
        "@": {
          "gml:id": ""
        },
        "gml:boundedBy": [{
          "gml:Envelope": [{
            "@": {
              "srsName": "EPSG:25832"
            },
            "gml:lowerCorner": "",
            "gml:upperCorner": ""
          }]
        }],
        "xplan:name": "",
        "xplan:nummer": "",
        "xplan:raeumlicherGeltungsbereich": [{
          "gml:Polygon": [{
            "@": {
              "srsName": "EPSG:25832",
              "gml:id": ""
            },
            "gml:exterior": [{
              "gml:LinearRing": [{
                "gml:posList": [{
                  "#text": "",
                  "@": {
                    "srsDimension": "2"
                  }
                }]
              }]
            }]
          }]
        }],
        "xplan:gemeinde": [{
          "xplan:XP_Gemeinde": [{
            "xplan:ags": "",
            "xplan:gemeindeName": "",
            "xplan:ortsteilName": ""
          }]
        }],
        "xplan:plangeber": [{
          "xplan:XP_Plangeber": [{
            "xplan:name": ""
          }]
        }],
        "xplan:planArt": 10001,
        "xplan:rechtsstand": 1000,
        "xplan:aufstellungsbeschlussDatum": "",
        "xplan:bereich": [{
          "@": {
            "xlink:href": ""
          }
        }]
      }]
    }]
  }]
};

const inputElement = document.getElementById('input');
inputElement.addEventListener('change', convertGML, false);

function convertGML() {
  const file = document.getElementById('input').files[0]
  const reader = new FileReader();
  reader.onload = function(evt) {
    var content = evt.target.result

    var options = {
      attributeNamePrefix: "",
      attrNodeName: "@",
      textNodeName: "#text",
      ignoreAttributes: false,
      ignoreNameSpace: false,
      allowBooleanAttributes: true,
      parseNodeValue: true,
      cdataPositionChar: "\\c",
      parseTrueNumberOnly: false,
      arrayMode: true
    };

    content = parser.parse(content, options);

    var inputID = Object.keys(content['ogr:FeatureCollection'][0]['gml:featureMember'][0])[0]

    const name = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:name'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:name'] = name

    const nummer = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:nummer'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:nummer'] = nummer

    const ags = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:ags'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:gemeinde'][0]['xplan:XP_Gemeinde'][0]['xplan:ags'] = ags

    const gemeindeName = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:gemeindeName'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:gemeinde'][0]['xplan:XP_Gemeinde'][0]['xplan:gemeindeName'] = gemeindeName

    const ortsteilName = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:ortsteilName'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:gemeinde'][0]['xplan:XP_Gemeinde'][0]['xplan:ortsteilName'] = ortsteilName

    const plangeber = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:plangeber'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:plangeber'][0]['xplan:XP_Plangeber'][0]['xplan:name'] = plangeber

    const planArt = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:planArt'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:planArt'] = planArt

    const rechtsstand = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:rechtsstand'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:rechtsstand'] = rechtsstand

    const aufstellungsbeschlussDatum = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:aufstellungsbeschlussDatum'];
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:aufstellungsbeschlussDatum'] = aufstellungsbeschlussDatum

    const bbox = content['ogr:FeatureCollection'][0]['gml:boundedBy'][0]['gml:Box'][0]['gml:coord']
    const bbox_e = bbox[0]['gml:X']
    const bbox_s = bbox[0]['gml:Y']
    const bbox_w = bbox[1]['gml:X']
    const bbox_n = bbox[1]['gml:Y']

    const lowerCorner = bbox_e + " " + bbox_s
    const upperCorner = bbox_w + " " + bbox_n

    template['xplan:XPlanAuszug'][0]['gml:boundedBy'][0]['gml:Envelope'][0]['gml:lowerCorner'] = lowerCorner
    template['xplan:XPlanAuszug'][0]['gml:boundedBy'][0]['gml:Envelope'][0]['gml:upperCorner'] = upperCorner

    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['gml:boundedBy'][0]['gml:Envelope'][0]['gml:lowerCorner'] = lowerCorner
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['gml:boundedBy'][0]['gml:Envelope'][0]['gml:upperCorner'] = upperCorner

    var boundary = content['ogr:FeatureCollection'][0]['gml:featureMember'][0][inputID][0]['ogr:geometryProperty'][0]['gml:Polygon'][0]['gml:outerBoundaryIs'][0]['gml:LinearRing'][0]['gml:coordinates'];
    boundary = boundary.split(' ');
    boundary = boundary.reverse();
    boundary = boundary.join();
    boundary = boundary.split(',').join(' ')

    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:raeumlicherGeltungsbereich'][0]['gml:Polygon'][0]['gml:exterior'][0]['gml:LinearRing'][0]['gml:posList'][0]['#text'] = boundary;

    const uuid_1 = "GML_" + uuidv4()
    template['xplan:XPlanAuszug'][0]['@']['gml:id'] = uuid_1

    const uuid_2 = "ID_" + uuidv4()
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][0]['xplan:BP_Bereich'][0]['@']['gml:id'] = uuid_2
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:bereich'][0]['@']['xlink:href'] = '#' + uuid_2

    const uuid_3 = "ID_" + uuidv4()
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][0]['xplan:BP_Bereich'][0]['xplan:gehoertZuPlan'][0]['@']['xlink:href'] = '#' + uuid_3
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['@']['gml:id'] = uuid_3

    const uuid_4 = "ID_" + uuidv4()
    template['xplan:XPlanAuszug'][0]['gml:featureMember'][1]['xplan:BP_Plan'][0]['xplan:raeumlicherGeltungsbereich'][0]['gml:Polygon'][0]['@']['gml:id'] = uuid_4

    var defaultOptions = {
      attributeNamePrefix: "",
      attrNodeName: "@",
      textNodeName: "#text",
      format: true,
      indentBy: "  ",
      supressEmptyNode: false
    };
    var compiler = new Parser(defaultOptions);
    content = compiler.parse(template);

    let zip = new JSZip();
    zip.file("xplan.gml", content);
    zip.generateAsync({
      type: "blob"
    }).then(function(content) {
      FileSaver.saveAs(content, slugify(name, {replacement: '_', strict: true}) + ".zip");
    });
  };
  reader.readAsText(file);

  input.files = new DataTransfer().files
}
