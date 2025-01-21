cwlVersion: v1.0
$namespaces:
  s: https://schema.org/
s:softwareVersion: 1.4.1
schemas:
  - http://schema.org/version/9.0/schemaorg-current-http.rdf
$graph:
  - class: Workflow
    id: water-bodies
    label: Water bodies detection based on NDWI and otsu threshold
    doc: Water bodies detection based on NDWI and otsu threshold
    requirements:
      - class: ScatterFeatureRequirement
      - class: SubworkflowFeatureRequirement
    inputs:
      aoi:
        label: area of interest
        doc: area of interest as a bounding box
        type: string
      epsg:
        label: EPSG code
        doc: EPSG code
        type: string
        default: EPSG:4326
      stac_items:
        label: Sentinel-2 STAC items
        doc: list of Sentinel-2 COG STAC items
        type: string[]
      bands:
        label: bands used for the NDWI
        doc: bands used for the NDWI
        type: string[]
        default:
          - green
          - nir
    outputs:
      - id: stac
        outputSource:
          - node_stac/stac_catalog
        type: Directory
    steps:
      node_water_bodies:
        run: '#detect_water_body'
        in:
          item: stac_items
          aoi: aoi
          epsg: epsg
          bands: bands
        out:
          - detected_water_body
        scatter: item
        scatterMethod: dotproduct
      node_stac:
        run: '#stac'
        in:
          item: stac_items
          rasters:
            source: node_water_bodies/detected_water_body
        out:
          - stac_catalog
  - class: Workflow
    id: detect_water_body
    label: Water body detection based on NDWI and otsu threshold
    doc: Water body detection based on NDWI and otsu threshold
    requirements:
      - class: ScatterFeatureRequirement
    inputs:
      aoi:
        doc: area of interest as a bounding box
        type: string
      epsg:
        doc: EPSG code
        type: string
        default: EPSG:4326
      bands:
        doc: bands used for the NDWI
        type: string[]
      item:
        doc: STAC item
        type: string
    outputs:
      - id: detected_water_body
        outputSource:
          - node_otsu/binary_mask_item
        type: File
    steps:
      node_crop:
        run: '#crop'
        in:
          item: item
          aoi: aoi
          epsg: epsg
          band: bands
        out:
          - cropped
        scatter: band
        scatterMethod: dotproduct
      node_normalized_difference:
        run: '#norm_diff'
        in:
          rasters:
            source: node_crop/cropped
        out:
          - ndwi
      node_otsu:
        run: '#otsu'
        in:
          raster:
            source: node_normalized_difference/ndwi
        out:
          - binary_mask_item
  - class: CommandLineTool
    id: crop
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /app
      ResourceRequirement:
        coresMax: 1
        ramMax: 512
    hints:
      DockerRequirement:
        dockerPull: ghcr.io/terradue/ogc-eo-application-package-hands-on/crop:1.5.0
    baseCommand:
      - python
      - '-m'
      - app
    arguments: []
    inputs:
      item:
        type: string
        inputBinding:
          prefix: '--input-item'
      aoi:
        type: string
        inputBinding:
          prefix: '--aoi'
      epsg:
        type: string
        inputBinding:
          prefix: '--epsg'
      band:
        type: string
        inputBinding:
          prefix: '--band'
    outputs:
      cropped:
        outputBinding:
          glob: '*.tif'
        type: File
  - class: CommandLineTool
    id: norm_diff
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /app
      ResourceRequirement:
        coresMax: 1
        ramMax: 512
    hints:
      DockerRequirement:
        dockerPull: ghcr.io/terradue/ogc-eo-application-package-hands-on/norm_diff:1.5.0
    baseCommand:
      - python
      - '-m'
      - app
    arguments: []
    inputs:
      rasters:
        type: File[]
        inputBinding:
          position: 1
    outputs:
      ndwi:
        outputBinding:
          glob: '*.tif'
        type: File
  - class: CommandLineTool
    id: otsu
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /app
      ResourceRequirement:
        coresMax: 1
        ramMax: 512
    hints:
      DockerRequirement:
        dockerPull: ghcr.io/terradue/ogc-eo-application-package-hands-on/otsu:1.5.0
    baseCommand:
      - python
      - '-m'
      - app
    arguments: []
    inputs:
      raster:
        type: File
        inputBinding:
          position: 1
    outputs:
      binary_mask_item:
        outputBinding:
          glob: '*.tif'
        type: File
  - class: CommandLineTool
    id: stac
    requirements:
      InlineJavascriptRequirement: {}
      EnvVarRequirement:
        envDef:
          PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
          PYTHONPATH: /app
      ResourceRequirement:
        coresMax: 1
        ramMax: 512
      InitialWorkDirRequirement:
        listing:
          - entryname: app.py
            entry: |-
              import click
              import pystac
              import rio_stac
              import shutil
              import os
              import datetime
              # Import rio_stac methods
              from rio_stac.stac import (
                  get_dataset_geom,
                  get_projection_info,
                  get_raster_info,
                  get_eobands_info,
                  bbox_to_geom,
              )

              @click.command(
                  short_help="Creates a STAC catalog",
                  help="Creates a STAC catalog with the water bodies",
              )
              @click.option(
                  "--input-item",
                  "item_urls",
                  help="STAC Item URL",
                  required=True,
                  multiple=True,
              )
              @click.option(
                  "--water-body",
                  "water_bodies",
                  help="Water body geotiff",
                  required=True,
                  multiple=True,
              )
              def to_stac(item_urls, water_bodies):

                  cat = pystac.Catalog(id="catalog", description="water-bodies")

                  for index, item_url in enumerate(item_urls):

                      item = pystac.read_file(item_url)
                      water_body = water_bodies[index]

                      os.mkdir(item.id)
                      shutil.copy(water_body, item.id)

                      #print(f"get raster info {str(get_raster_info(src_dst=water_body))}")
                      out_item = rio_stac.stac.create_stac_item(
                          source=water_body,
                          input_datetime=item.datetime,
                          id=item.id,
                          extensions=[
                            f"https://stac-extensions.github.io/processing/v1.2.0/schema.json",
                          ],
                          properties={
                            "processing:software": [
                              {
                                "name": "ZOO-Project-DRU",
                                "version": "2.0.1",
                                "url": "https://github.com/ZOO-Project/ZOO-Project.git"
                              },
                              {
                                "name": "cwltool",
                                "version": "3.1.20240508115724",
                                "url": "https://github.com/common-workflow-language/cwltool/releases/tag/3.1.20240508115724"
                              },
                              {
                                "name": "ogc-eo-application-package-hands-on/stage",
                                "version": "1.3.2",
                                "url": "https://github.com/Terradue/ogc-eo-application-package-hands-on/pkgs/container/ogc-eo-application-package-hands-on%2Fstage",
                                "image": "ghcr.io/terradue/ogc-eo-application-package-hands-on/stage:1.3.2",
                              },
                              {
                                "name": "ogc-eo-application-package-hands-on/stac",
                                "version": "1.5.0",
                                "url": "https://github.com/Terradue/ogc-eo-application-package-hands-on/pkgs/container/ogc-eo-application-package-hands-on%2Fstac",
                                "image": "ghcr.io/terradue/ogc-eo-application-package-hands-on/stac:1.5.0",
                              },
                              {
                                "name": "ogc-eo-application-package-hands-on/crop",
                                "version": "1.5.0",
                                "url": "https://github.com/Terradue/ogc-eo-application-package-hands-on/pkgs/container/ogc-eo-application-package-hands-on%2Fcrop",
                                "image": "ghcr.io/terradue/ogc-eo-application-package-hands-on/crop:1.5.0",
                              },
                              {
                                "name": "ogc-eo-application-package-hands-on/norm_diff",
                                "version": "1.5.0",
                                "url": "https://github.com/Terradue/ogc-eo-application-package-hands-on/pkgs/container/ogc-eo-application-package-hands-on%2Fnorm_diff",
                                "image": "ghcr.io/terradue/ogc-eo-application-package-hands-on/norm_diff:1.5.0",
                              },
                              {
                                "name": "ogc-eo-application-package-hands-on/otsu",
                                "version": "1.5.0",
                                "url": "https://github.com/Terradue/ogc-eo-application-package-hands-on/pkgs/container/ogc-eo-application-package-hands-on%2Fotsu",
                                "image": "ghcr.io/terradue/ogc-eo-application-package-hands-on/otsu:1.5.0",
                              },
                            ],
                            "processing:facility": "GeoLabs - D144 - Provenance demonstration - OGC Testbed-20 dedicated ressources",
                            "processing:datetime": 
                              str(datetime.datetime.now())
                          },
                          asset_roles=["data", "visual"],
                          asset_href=os.path.basename(water_body),
                          asset_name="data",
                          with_proj=True,
                          with_raster=True,
                          with_eo=True,
                      )

                      cat.add_items([out_item])

                  cat.normalize_and_save(
                      root_href="./", catalog_type=pystac.CatalogType.SELF_CONTAINED
                  )


              if __name__ == "__main__":
                  to_stac()
    hints:
      DockerRequirement:
        dockerPull: ghcr.io/terradue/ogc-eo-application-package-hands-on/stac:1.5.0
    baseCommand:
      - python
      - '-m'
      - app
    arguments: []
    inputs:
      item:
        type:
          type: array
          items: string
          inputBinding:
            prefix: '--input-item'
      rasters:
        type:
          type: array
          items: File
          inputBinding:
            prefix: '--water-body'
    outputs:
      stac_catalog:
        outputBinding:
          glob: .
        type: Directory
