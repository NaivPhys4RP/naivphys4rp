// Fill out your copyright notice in the Description page of Project Settings.


#include "UFluidSmartMedium.h" // <-- THIS MUST BE FIRST
#include "DrawDebugHelpers.h"
#include <omp.h>
#include "Algo/Reverse.h"
#include "Misc/Paths.h"

//constructor
AUFluidSmartMedium::AUFluidSmartMedium()
{
    this->Force_Field_Trajectory={FVector(287.000000,-252.441864,104.000000), FVector(287.000000,-252.441864,109.000000)};
    this->Force_Field={};
    Selected_Target_Particles={};
    this->Force_Field_Intensity=5.0f;
    this->Force_Field_Volume_Density=100;
    this->Force_Field_Area_Density=1.0f;
    Should_Transport=true;
    TargetFluid=nullptr;
    Force_Vector_Thickness=0.0f;
    Force_Vector_Arrow_Size=1.0;
    Should_Show_Force_Field=true;
    PrimaryActorTick.bCanEverTick = true;
    force_field_trajectory_pointer=-1;
    Force_Field_Treshold=15.0f;
    Should_Reverse_Force_Field=false;
    Reverse_Status=Should_Reverse_Force_Field;
    Force_Field_Angle=160.0f;
    Intensity_Multiplier=1.0f;
    Intensity_Treshold=6.0f;

}

//destructor
AUFluidSmartMedium::~AUFluidSmartMedium()
{
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- KILLING Medium---------------------------------------"));
}


// Called when the game starts or when spawned
void AUFluidSmartMedium::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Warning,TEXT("Begin play!"));
    //AUFluidSmartMedium::BuildForceField();
}


// Called every frame
void AUFluidSmartMedium::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if(Reverse_Status != Should_Reverse_Force_Field){
       Reverse_Status = Should_Reverse_Force_Field;
       Algo::Reverse(this->Force_Field_Trajectory);
    }
    if(this->Should_Transport && AUFluidSmartMedium::BuildForceField_V2())
       AUFluidSmartMedium::Transport();
}


// build force field
bool AUFluidSmartMedium::BuildForceField(){
    //clear force field
    this->Force_Field.Empty();
    FVector vec1,vec2,unit_vec, normal_vec;
    float norm_vec,rx,ry,rz,r;
    //spread forces over field trajectory
    for(int i=0;i<this->Force_Field_Trajectory.Num()-1;i++){
        //compute unit vector between two vectors
        vec1=this->Force_Field_Trajectory[i];
        vec2=this->Force_Field_Trajectory[i+1];
        unit_vec=vec2-vec1;
        //compute normal vector
        int pivot=-1;
        for(int l=0;l<3;l++){
            if(unit_vec[l]>0.0f){
                pivot=l;
                break;
            }
        }

        if(pivot==-1)
            continue; //null vector force

        //spread forces over volumic segment of field trajectory
        for(int j=0;j<this->Force_Field_Volume_Density;j++){
            //spread forces over surfaces of volumic segment
            rx=FMath::RandRange(-this->Force_Field_Intensity,this->Force_Field_Intensity);
            ry=FMath::RandRange(-this->Force_Field_Intensity,this->Force_Field_Intensity);
            rz=FMath::RandRange(-this->Force_Field_Intensity,this->Force_Field_Intensity);
            //adjust rz; or rx,ry,rz to be a normal vector
            if(pivot==0)
                //update rx
                rx=-(unit_vec[1]*ry+unit_vec[2]*rz)/unit_vec[0];
            else
                if(pivot==1)
                    //update ry
                    ry=-(unit_vec[0]*rx+unit_vec[2]*rz)/unit_vec[1];
                else
                    //update rz
                    rz=-(unit_vec[1]*ry+unit_vec[0]*rx)/unit_vec[2];

            normal_vec=FVector(rx,ry,rz);
            //normalize vectors
            norm_vec=FMath::Sqrt(FMath::Pow(unit_vec.X, 2) + FMath::Pow(unit_vec.Y, 2) + FMath::Pow(unit_vec.Z, 2));
            if(!(norm_vec>0.0f))
                continue; //skip if the force is null
            unit_vec=this->Force_Field_Intensity*unit_vec/norm_vec;

            norm_vec=FMath::Sqrt(FMath::Pow(normal_vec.X, 2) + FMath::Pow(normal_vec.Y, 2) + FMath::Pow(normal_vec.Z, 2));
            if(!(norm_vec>0.0f))
                continue; //skip if the force is null
            r=FMath::RandRange(-this->Force_Field_Area_Density,this->Force_Field_Area_Density);
            normal_vec=r*normal_vec/norm_vec;

            //update force direction
            unit_vec=unit_vec+normal_vec;


            //normalize resulting force vector
            norm_vec=FMath::Sqrt(FMath::Pow(unit_vec.X, 2) + FMath::Pow(unit_vec.Y, 2) + FMath::Pow(unit_vec.Z, 2));
            if(!(norm_vec>0.0f))
                continue; //skip if the force is null
            unit_vec=unit_vec/norm_vec;

            unit_vec=unit_vec*this->Force_Field_Intensity;

            //compute the force origin
           if(FMath::RandRange(0.0f,1.0f)<=0.1f){
                normal_vec=vec1;
           }
           else{
            normal_vec=vec1 - normal_vec;
           }

            //adding force direction and vector in the force field
            this->Force_Field.Emplace(normal_vec);//force origin
            this->Force_Field.Emplace(unit_vec); //force vector

        }


    }

    return true;
}

float AUFluidSmartMedium::DistanceToMedium(FVector A, FVector B, FVector C){
    float distance=0.0f;
    FVector direction=C-B;
    FVector support=A-B;
    float norm_vec=FMath::Sqrt(FMath::Pow(direction.X, 2) + FMath::Pow(direction.Y, 2) + FMath::Pow(direction.Z, 2));
    if(norm_vec>0.0f){
        direction=direction/norm_vec;
        float t=FVector::DotProduct(direction, support);
        FVector M=B+direction*t;
        direction=M-A;
        distance=FMath::Sqrt(FMath::Pow(direction.X, 2) + FMath::Pow(direction.Y, 2) + FMath::Pow(direction.Z, 2));
    }else{
        direction=A-B;
        distance=FMath::Sqrt(FMath::Pow(direction.X, 2) + FMath::Pow(direction.Y, 2) + FMath::Pow(direction.Z, 2));
    }
    return distance;
}
// build force field
bool AUFluidSmartMedium::BuildForceField_V2(){
    //clear force field
    if(!this->TargetFluid || !this->TargetFluid->Should_Use_Fluid)
        return false;
    Selected_Target_Particles.Empty();
    this->Force_Field.Empty();
    FVector direc,vec1,vec2,vec,unit_vec, normal_vec;
    float norm_vec,rx,ry,rz,r,AimAtAngle, min_distance;
    int target_point;
    //spread forces over field trajectory
    if(this->Force_Field_Trajectory.Num()<1)
        return false;


   /*if (force_field_trajectory_pointer<this->Force_Field_Trajectory.Num()-1){
         force_field_trajectory_pointer++;
   }*/
    for(int i=0;i<this->TargetFluid->U_FluidEmitter->U_FluidParticles.Num();i++){
         vec1=this->TargetFluid->U_FluidEmitter->U_FluidParticles[i]->U_StaticMeshActor->GetActorLocation();

        //searching right index
        min_distance=Force_Field_Treshold;
        target_point=-1;
        for(int n=0;n<this->Force_Field_Trajectory.Num()-1;n++){
            //compute direction vector
            direc=this->Force_Field_Trajectory[n+1]-Force_Field_Trajectory[n];

            norm_vec=FMath::Sqrt(FMath::Pow(direc.X, 2) + FMath::Pow(direc.Y, 2) + FMath::Pow(direc.Z, 2));
            if(!(norm_vec>0.0f))
                return false; //return false if no transfer
            direc=direc/norm_vec;

            //compute unit vector between two vectors
            vec2=this->Force_Field_Trajectory[n];
            unit_vec=vec2-vec1;
            norm_vec=FMath::Sqrt(FMath::Pow(unit_vec.X, 2) + FMath::Pow(unit_vec.Y, 2) + FMath::Pow(unit_vec.Z, 2));
            unit_vec=unit_vec/norm_vec;
            //compute absolute angle between two vectors
            AimAtAngle = abs(FMath::RadiansToDegrees(acosf(FVector::DotProduct(direc, unit_vec))));
            UE_LOG(LogTemp, Warning, TEXT("///////////////////////// MATCH CHECKKING: d=%f, nbr=%d, Alpha=%f ///////////////////////////////"), norm_vec, this->Force_Field_Trajectory.Num(), AimAtAngle);
            if(AimAtAngle<Force_Field_Angle){
                target_point=n;
                UE_LOG(LogTemp, Warning, TEXT("///////////////////////// MATCH FOUND = %d ///////////////////////////////"),n);
                break;//stop searching
            }else{
                target_point=n+1;
            }
        }
        if(target_point<0)
            target_point=0;
        //compute unit vector between two vectors
        vec2=this->Force_Field_Trajectory[target_point];
        unit_vec=vec2-vec1;
        norm_vec=FMath::Sqrt(FMath::Pow(unit_vec.X, 2) + FMath::Pow(unit_vec.Y, 2) + FMath::Pow(unit_vec.Z, 2));
        if((norm_vec>min_distance) || !(norm_vec>0.0f))
            continue; //particle is too far from or too close to target
        //scale force
        //compute the distance of the particle to the tube
        FVector A=vec1;
        FVector B=vec2;
        FVector C=(target_point==0)?B:this->Force_Field_Trajectory[target_point-1];
        float distance=AUFluidSmartMedium::DistanceToMedium( A, B, C);
        float distance1=AUFluidSmartMedium::DistanceToMedium( FVector(2.0f,0.0f,0.0f), FVector(5.0f,0.0f,-8.0f), FVector(5.0f,0.0f,9.0f));
        float distance2=AUFluidSmartMedium::DistanceToMedium( FVector(2.0f,0.0f,0.0f), FVector(5.0f,0.0f,8.0f), FVector(5.0f,0.0f,9.0f));
        float distance3=AUFluidSmartMedium::DistanceToMedium( FVector(0.0f,0.0f,0.0f), FVector(1.0f,0.0f,0.0f), FVector(0.0f,0.0f,1.0f));
        UE_LOG(LogTemp, Warning, TEXT("------------------------------------- DISTANCE1 TO TUBE = %f ------------------------------------- "),distance1);
        UE_LOG(LogTemp, Warning, TEXT("-------------------------------------  DISTANCE2 TO TUBE = %f ------------------------------------- "),distance2);
        UE_LOG(LogTemp, Warning, TEXT("-------------------------------------  DISTANCE3 TO TUBE = %f ------------------------------------- "),distance3);
        UE_LOG(LogTemp, Warning, TEXT("+++++++++++++++++++++++++++++++++++++ DISTANCE TO TUBE = %f +++++++++++++++++++++++++++++++++++"),distance);
        if(distance>this->Force_Field_Area_Density && target_point>0)
            continue;   //return if the particle is not in the tube
        float multiplier_vec=FMath::Pow(Intensity_Multiplier,target_point)*this->Force_Field_Intensity;
        multiplier_vec = (multiplier_vec>Intensity_Treshold)?Intensity_Treshold:multiplier_vec;
        unit_vec= multiplier_vec*unit_vec/norm_vec;
        this->Force_Field.Emplace(unit_vec); //force vector
        Selected_Target_Particles.Emplace(i); //corresponding particle

    }

    return true;
}


// apply force field to transport fluid
bool AUFluidSmartMedium::Transport(){

    FVector vec1,vec2,unit_vec, normal_vec;
    float norm_vec,rx,ry,rz,r;
    UStaticMeshComponent* ParticleComponent;

    for(int i=0;i<this->Selected_Target_Particles.Num();i=i+1){
       if(this->Should_Show_Force_Field){
           vec1=this->TargetFluid->U_FluidEmitter->U_FluidParticles[Selected_Target_Particles[i]]->U_StaticMeshActor->GetActorLocation();
           vec2=vec1+this->Force_Field[i];
           DrawDebugDirectionalArrow(GetWorld(), vec1,vec2, Force_Vector_Arrow_Size,FColor::Blue, false, 1.0f,0,Force_Vector_Thickness);
       }
       //add force impulse

       ParticleComponent =  Cast<AStaticMeshActor>(this->TargetFluid->U_FluidEmitter->U_FluidParticles[Selected_Target_Particles[i]]->U_StaticMeshActor)->GetStaticMeshComponent();
       ParticleComponent->AddImpulse(this->Force_Field[i]);
    }
    return true;
}
