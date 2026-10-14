// Fill out your copyright notice in the Description page of Project Settings.


#include "UParaSimHUD.h"
#include "Framework/Application/SlateApplication.h"
#include "Engine.h"
#include "Styling/SlateStyleRegistry.h"
#include "Framework/Commands/Commands.h"
#include "Slate/SlateGameResources.h"
#include "Interfaces/IPluginManager.h"
#include "Runtime/Engine/Classes/Engine/TextureRenderTarget2D.h"
#include "Runtime/Engine/Public/Slate/SceneViewport.h"
#include "Widgets/SViewport.h"
#include "Widgets/SToolTip.h"
#include "Widgets/SWindow.h"


/*       ********************************************************************************** */
//constructor

UUParaSimWidget::UUParaSimWidget(const FObjectInitializer &ObjectInitializer):Super(ObjectInitializer)
{
}

//initialize the widget at start
void UUParaSimWidget::NativeConstruct()
{
  Super::NativeConstruct();
  StoreWidgetAnimations();
  ComboFadeAnimation = GetAnimationByName(TEXT("ComboFade"));
  ComboShakeAnimation = GetAnimationByName(TEXT("ComboShake"));
}

//Update the widget
void UUParaSimWidget::UpdateComboCount(int32 Value)
{
  // only update if more than one hit
  if (TXTCombo && Value > 1)
  {
    if (TXTCombo->Visibility == ESlateVisibility::Hidden)
    {
      TXTCombo->SetVisibility(ESlateVisibility::Visible);
    }
    TXTCombo->SetText(FText::FromString((FString::FromInt(Value) + "x Combo")));
    if (ComboShakeAnimation)
    {
      PlayAnimation(ComboShakeAnimation, 0.f, 1, EUMGSequencePlayMode::Forward, 1.f);
    }
    if (ComboFadeAnimation)
    {
      PlayAnimation(ComboFadeAnimation, 0.f, 1, EUMGSequencePlayMode::Forward, 1.f);
    }
  }
}

//Reset the widget
void UUParaSimWidget::ResetCombo()
{
  GEngine->AddOnScreenDebugMessage(-1, 3.f, FColor::Orange, __FUNCTION__);
  if (TXTCombo)
  {
    TXTCombo->SetVisibility(ESlateVisibility::Hidden);
  }
}

//get animation by name
UWidgetAnimation* UUParaSimWidget::GetAnimationByName(FName AnimationName) const
{
  UWidgetAnimation* const* WidgetAnimation = AnimationsMap.Find(AnimationName);
  if (WidgetAnimation)
  {
    return *WidgetAnimation;
  }
  return nullptr;
}


//store animation widget
void UUParaSimWidget::StoreWidgetAnimations()
{
  AnimationsMap.Empty();
  UProperty* Prop = GetClass()->PropertyLink;
  // check each property of this class
  while (Prop)
  {
    // only evaluate object properties, skip rest
    if (Prop->GetClass() == UObjectProperty::StaticClass())
    {
      UObjectProperty* ObjProp = Cast<UObjectProperty>(Prop);
      // only get back properties that are of type widget animation
      if (ObjProp->PropertyClass == UWidgetAnimation::StaticClass())
      {
        UObject* Obj = ObjProp->GetObjectPropertyValue_InContainer(this);
        // only get back properties that are of type widget animation
        UWidgetAnimation* WidgetAnimation = Cast<UWidgetAnimation>(Obj);
        // if casting worked update map with new animation
        if (WidgetAnimation && WidgetAnimation->MovieScene)
        {
          FName AnimName = WidgetAnimation->MovieScene->GetFName();
          GEngine->AddOnScreenDebugMessage(-1, 4.5f, FColor::Magenta, AnimName.ToString());
          AnimationsMap.Add(AnimName, WidgetAnimation);
        }
      }
    }
    Prop = Prop->PropertyLinkNext;
  }
}


/*       *********************************************************************************** */
//constructor
AUParaSimHUD::AUParaSimHUD(const FObjectInitializer &ObjectInitializer):Super(ObjectInitializer)
{

}

//build the HUD at start and add HUD to viewport
void AUParaSimHUD::BeginPlay()
{
  Super::BeginPlay();
  if (HitComboWidgetClass)
  {
    HitComboWidget = CreateWidget<UUParaSimWidget>(GetWorld(), HitComboWidgetClass);
    /** Make sure widget was created */
    if (HitComboWidget)
    {
      /** Add it to the viewport */
      HitComboWidget->AddToViewport();
    }
  }
}

//Function to update HUD
void AUParaSimHUD::UpdateComboCount(int32 Value)
{
  if (HitComboWidget)
  {
    HitComboWidget->UpdateComboCount(Value);
  }
}

//Reset the widget
void AUParaSimHUD::ResetCombo()
{

  if (HitComboWidget)
  {
    HitComboWidget->ResetCombo();
  }
}

// Primary draw call for the HUD.
void AUParaSimHUD::DrawHUD(){
    Super::DrawHUD();
}

void AUParaSimHUD::Tick(float DeltaSeconds){
        Super::Tick(DeltaSeconds);
}





/*       *********************************************************************************** */





/*       *********************************************************************************** */



void UUParaSimSceneCaptureComponent2D::Activate(bool bReset)
{
    Super::Activate();
     //UE_LOG(LogTemp, Warning, TEXT(" CALLING UUParaSimSceneCaptureComponent2D::Activate!"));
    // Assign Render texture to shared module variale
    IUParaSimScene::Get().SetTextureRenderTarget2D(this->TextureTarget);
}

#if WITH_EDITOR
void UUParaSimSceneCaptureComponent2D::OnRegister()
{
    Super::OnRegister();
    //UE_LOG(LogTemp, Warning, TEXT(" CALLING UUParaSimSceneCaptureComponent2D::OnRegister!"));
    // Assign Render texture to shared module variale
    IUParaSimScene::Get().SetTextureRenderTarget2D(this->TextureTarget);
}
#endif

/*       *********************************************************************************** */

FUParaSimViewportClient::FUParaSimViewportClient(int slate_ID){
    this->Slate_ID=slate_ID;
}

void FUParaSimViewportClient::Draw(FViewport * Viewport, FCanvas * Canvas)
{
    // Clear entire canvas
    Canvas->Clear(FLinearColor::Black);
     //UE_LOG(LogTemp, Warning, TEXT("Drawing FUParaSimViewportClient::Draw!"));
    // Draw SceenCaptureComponent texture to entire canvas
    auto TextRenderTarget2D = IUParaSimScene::Get().GetTextureRenderTarget2D(this->Slate_ID);



    if (TextRenderTarget2D.IsValid() && TextRenderTarget2D->Resource != nullptr)
    {
        //UE_LOG(LogTemp, Warning, TEXT("Drawing FUParaSimViewportClient::Draw! is working"));
        FCanvasTileItem TileItem(FVector2D(0, 0), TextRenderTarget2D->Resource,
            FVector2D(Viewport->GetRenderTargetTexture()->GetSizeX(), Viewport->GetRenderTargetTexture()->GetSizeY()),
            FLinearColor::White);
        TileItem.BlendMode = ESimpleElementBlendMode::SE_BLEND_Opaque;
        Canvas->DrawItem(TileItem);
    }
}

bool FUParaSimViewportClient::InputKey(FViewport * Viewport, int32 ControllerId, FKey Key, EInputEvent Event, float AmountDepressed, bool bGamepad)
{
    return false;
}

bool FUParaSimViewportClient::InputAxis(FViewport * Viewport, int32 ControllerId, FKey Key, float Delta, float DeltaTime, int32 NumSamples, bool bGamepad)
{
    return false;
}

bool FUParaSimViewportClient::InputGesture(FViewport * Viewport, EGestureEvent GestureType, const FVector2D & GestureDelta, bool bIsDirectionInvertedFromDevice)
{
    return false;
}


void SUParaSimViewport::Construct(const FArguments& InArgs)
{
    // Create Viewport Widget
    Viewport = SNew(SViewport)
        .IsEnabled(true)
        .EnableGammaCorrection(false)
        .ShowEffectWhenDisabled(false)
        .EnableBlending(true)
        .ToolTip(SNew(SToolTip).Text(FText::FromString("SUParaSimViewport")));

    UWorld* cworld=InArgs._CWORLD.Get();
    int slate_ID=InArgs._slate_ID.Get();
    // Create Viewport Client
    PlaySceneViewportClient = MakeShareable(new FUParaSimViewportClient(slate_ID));

    // Create Scene Viewport
    SceneViewport = MakeShareable(new FSceneViewport(PlaySceneViewportClient.Get(), Viewport));
    //cworld->GetGameViewport()->bDisableWorldRendering=false;
    //SceneViewport=MakeShareable(cworld->GetGameViewport()->GetGameViewport());
    // Assign SceneViewport to Viewport widget. It needed for rendering
    Viewport->SetViewportInterface(SceneViewport.ToSharedRef());

    // Assing Viewport widget for our custom PlayScene Viewport
    this->ChildSlot
        [
            Viewport.ToSharedRef()
        ];
}

void SUParaSimViewport::Tick(const FGeometry & AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
    // Call FViewport each engine tick
    //UE_LOG(LogTemp, Warning, TEXT("Drawing SUParaSimViewport::Tick!"));
    SceneViewport->Draw();
}

int UUParaSimSceneSlate::NBR_OF_PARTICLES=30;
bool UUParaSimSceneSlate::RUNNING=false;
TArray<TSharedPtr<UUParaSimSceneSlate>> UUParaSimSceneSlate::PlaySceneSlate={};


UUParaSimSceneSlate::UUParaSimSceneSlate(UWorld* cworld, int ID)
    : PlaySceneWindowWidth(640)
    , PlaySceneWindowHeight(480)
{
    // Create SWindow
    PlaySceneWindow = SNew(SWindow)
        .Title(FText::FromString(FString::Printf(TEXT("UParaSim - Secondary World (Particle %d)"),ID)))
        .ScreenPosition(FVector2D(0, 0))
        .ClientSize(FVector2D(PlaySceneWindowWidth, PlaySceneWindowHeight))
        .AutoCenter(EAutoCenter::PreferredWorkArea)
        .UseOSWindowBorder(true)
        .SaneWindowPlacement(false)
        .SizingRule(ESizingRule::UserSized);

    FSlateApplication::Get().AddWindow(PlaySceneWindow.ToSharedRef());
    this->Slate_ID=ID;
    // Assign window events delegator
    InDelegate.BindRaw(this, &UUParaSimSceneSlate::OnWindowClosed);
    PlaySceneWindow->SetOnWindowClosed(InDelegate);

    // Create and assign viewport to window
    PlaySceneViewport = SNew(SUParaSimViewport).CWORLD(cworld).slate_ID(this->Slate_ID);
    PlaySceneWindow->SetContent(PlaySceneViewport.ToSharedRef());
}

UUParaSimSceneSlate::~UUParaSimSceneSlate()
{
    InDelegate.Unbind();
}

void UUParaSimSceneSlate::Initialize(UWorld* cworld)
{
    // Create single instance of PlaySceneSlate
    if (!UUParaSimSceneSlate::RUNNING)
    {

            for(int i=0; i<UUParaSimSceneSlate::NBR_OF_PARTICLES;i++){
              if(UUParaSimSceneSlate::PlaySceneSlate.Num()<UUParaSimSceneSlate::NBR_OF_PARTICLES){
                UUParaSimSceneSlate::PlaySceneSlate.Emplace(nullptr);
               }
                UUParaSimSceneSlate::PlaySceneSlate[i]=MakeShareable(new UUParaSimSceneSlate(cworld,i));
            }

        UUParaSimSceneSlate::RUNNING=true;
    }else{
        UUParaSimSceneSlate::Shutdown();
    }
}

void UUParaSimSceneSlate::Shutdown()
{

    if (UUParaSimSceneSlate::RUNNING)
    {
        for(int i=0; i<UUParaSimSceneSlate::NBR_OF_PARTICLES;i++){
            if (UUParaSimSceneSlate::PlaySceneSlate[i].IsValid() && UUParaSimSceneSlate::PlaySceneSlate[i] != nullptr){
                FSlateApplicationBase::Get().RequestDestroyWindow(UUParaSimSceneSlate::PlaySceneSlate[i]->PlaySceneWindow.ToSharedRef());
                UUParaSimSceneSlate::PlaySceneSlate[i].Reset();
                UUParaSimSceneSlate::PlaySceneSlate[i] = nullptr;
            }
        }
        UUParaSimSceneSlate::RUNNING=false;
    }

}


void UUParaSimSceneSlate::OnWindowClosed(const TSharedRef<SWindow>& Window)
{
   //UUParaSimSceneSlate::Shutdown();
}


/*       *********************************************************************************** */


TSharedPtr< FSlateStyleSet > FUParaSimSceneStyle::StyleInstance = NULL;

void FUParaSimSceneStyle::Initialize()
{
    if (!StyleInstance.IsValid())
    {
        StyleInstance = Create();
        FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
    }
}

void FUParaSimSceneStyle::Shutdown()
{
    FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
    ensure(StyleInstance.IsUnique());
    StyleInstance.Reset();
}

FName FUParaSimSceneStyle::GetStyleSetName()
{
    static FName StyleSetName(TEXT("PlaySceneStyle"));
    return StyleSetName;
}

#define IMAGE_BRUSH( RelativePath, ... ) FSlateImageBrush( Style->RootToContentDir( RelativePath, TEXT(".png") ), __VA_ARGS__ )
#define BOX_BRUSH( RelativePath, ... ) FSlateBoxBrush( Style->RootToContentDir( RelativePath, TEXT(".png") ), __VA_ARGS__ )
#define BORDER_BRUSH( RelativePath, ... ) FSlateBorderBrush( Style->RootToContentDir( RelativePath, TEXT(".png") ), __VA_ARGS__ )
#define TTF_FONT( RelativePath, ... ) FSlateFontInfo( Style->RootToContentDir( RelativePath, TEXT(".ttf") ), __VA_ARGS__ )
#define OTF_FONT( RelativePath, ... ) FSlateFontInfo( Style->RootToContentDir( RelativePath, TEXT(".otf") ), __VA_ARGS__ )

const FVector2D Icon16x16(16.0f, 16.0f);
const FVector2D Icon20x20(20.0f, 20.0f);
const FVector2D Icon40x40(40.0f, 40.0f);

TSharedRef< FSlateStyleSet > FUParaSimSceneStyle::Create()
{
    TSharedRef< FSlateStyleSet > Style = MakeShareable(new FSlateStyleSet("PlaySceneStyle"));
    Style->SetContentRoot(TEXT("/mnt/Datadisk/franklin/UParaSim/Content/Resources"));

    Style->Set("UParaSim.OpenPluginWindow", new IMAGE_BRUSH(TEXT("logo_short"), Icon40x40));

    return Style;
}

#undef IMAGE_BRUSH
#undef BOX_BRUSH
#undef BORDER_BRUSH
#undef TTF_FONT
#undef OTF_FONT

void FUParaSimSceneStyle::ReloadTextures()
{
    if (FSlateApplication::IsInitialized())
    {
        FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
    }
}

const ISlateStyle& FUParaSimSceneStyle::Get()
{
    return *StyleInstance;
}



/*       *********************************************************************************** */

#define LOCTEXT_NAMESPACE "FUParaSimModule"
void FUParaSimSceneCommands::RegisterCommands()
{
    UI_COMMAND(OpenPluginWindow, "UParaSim", "Bring up PlayScene window", EUserInterfaceActionType::Button, FInputGesture());
}
#undef LOCTEXT_NAMESPACE
