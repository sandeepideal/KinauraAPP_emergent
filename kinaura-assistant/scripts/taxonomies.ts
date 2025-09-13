export const CONCERNS = [
  "redness","rosacea","pigmentation","sun_damage","pre_event_glow","fine_lines","wrinkles",
  "skin_laxity_face","jawline_neck_contour","texture","acne","acne_scars","pores",
  "cellulite","body_contour","hair_loss","vaginal_rejuvenation","recovery","inflammation","detox","stress_sleep","performance"
] as const;
export type Concern = typeof CONCERNS[number];

export const DEVICES = [
  "VISIA-7",
  "Wellness Tower",
  "Sciton mJOULE (BBL HERO / MOXI / SkinTyte)",
  "InMode Ignite (Morpheus8 / FaceTite / BodyTite)",
  "MCT (Meta Cell Technology)",
  "Emuage Lab",
  "Ultraformer MPT (HIFU)",
  "Weberneedle Endolaser",
  "Fotona DYNAMIS MAX (Er:YAG / Nd:YAG)",
  "AirPod Revive Hydroxy (mHBOT + H2)",
  "Ammortal Chamber (PEMF/PEF + PBM + H2 + Vibro-Acoustic)",
  "HydraFacial Syndeo MD"
] as const;
export type Device = typeof DEVICES[number];
