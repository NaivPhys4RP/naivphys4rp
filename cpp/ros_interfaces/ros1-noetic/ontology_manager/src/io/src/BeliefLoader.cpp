/**
 * Copyright 2022 University of Bremen, Institute for Artificial Intelligence
 * Author(s): Franklin Kenghagho Kenfack <fkenghag@cs.uni-bremen.de>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include <uima/api.hpp>

#include <pcl/point_types.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/passthrough.h>
#include <pcl/features/shot_omp.h>
#include <pcl/registration/ia_ransac.h>
#include <pcl/features/fpfh.h>

#include <flann/flann.h>
#include <flann/io/hdf5.h>

//Caffe
#include <caffe/caffe.hpp>

//RS
#include <rs/types/all_types.h>
#include <rs/scene_cas.h>
#include <rs/utils/time.h>
#include <rs/DrawingAnnotator.h>

#include <ros/package.h>

#include <rs/recognition/CaffeProxy.h>


using namespace uima;

class BeliefLoader : public DrawingAnnotator
{
private:

  int color;
public:

  BeliefLoader(): DrawingAnnotator(__func__)
  {
    color=0;
  }

  TyErrorId initialize(AnnotatorContext &ctx)
  {
    outInfo("initializing BeliefLoader");
   
    if(ctx.isParameterDefined("ccolor"))
    {
      ctx.extractValue("ccolor", color);
    }
    return UIMA_ERR_NONE;
  }

  TyErrorId destroy()
  {
    outInfo("destroying BeliefLoader");
    return UIMA_ERR_NONE;
  }

  TyErrorId processWithLock(CAS &tcas, ResultSpecification const &res_spec)
  {
    MEASURE_TIME;
    outInfo("running BeliefLoader");
    return UIMA_ERR_NONE;
  }

  void drawImageWithLock(cv::Mat &disp)
  {
    disp = color.clone();
  }

  void fillVisualizerWithLock(pcl::visualization::PCLVisualizer &visualizer, bool firstRun)
  {
    const std::string name = "color";

  }
};

MAKE_AE(BeliefLoader)
