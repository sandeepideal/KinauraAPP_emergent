# KinAura Branding Guide

## Asset Organization

### Brand Assets Location
- **Primary location**: `/frontend/assets/brand/`
- **Public access**: `/frontend/public/brand/`

### Available Assets
- `kinaura-logo.svg` - Full KinAura logo with text
- `kinaura-symbol.svg` - Symbol-only version for app icons
- `kinaura-splash.png` - Luxury splash background with ivory + gold kintsugi veins

## Color Palette

### Primary Colors
- **Gold Primary**: `#B88E35` (`--ka-gold-600`)
- **Gold Accent**: `#CFA544` (`--ka-gold-500`)
- **Ivory Base**: `#FAFAF7` (`--ka-ivory-100`)
- **Ink Dark**: `#1B1B1B` (`--ka-ink-50`)

### Usage Guidelines
- Gold: Brand elements, accents, CTAs, focus states
- Ivory: Backgrounds, cards, panels
- Ink: Primary text, high contrast elements
- Use the CSS custom properties for consistency

## App Icon Guidelines

### Design Principles
- **Minimalist**: Clean, premium appearance
- **No Text**: App Store/Play Store compliance
- **High Legibility**: Clear at all sizes (16px to 1024px)
- **Symbol Only**: Use `kinaura-symbol.svg`

### Platform Specific
- **iOS**: Symbol with 18% padding around viewBox
- **Android**: Adaptive icon with ivory background
- **Web/PWA**: SVG with maskable support

## Splash Screen Guidelines

### Background
- Base color: Ivory `#FAFAF7`
- Subtle gold kintsugi veins pattern
- Centered KinAura symbol at 24-28% of shorter screen dimension

### Implementation
- Use `kinaura-splash.png` as background image
- Background size: `cover`
- Background position: `center`
- Minimum duration, non-interactive

## App Background Implementation

### Universal Background
All app screens inherit the luxury splash background:

```jsx
// Applied in App.js
<div 
  className="kinaura-app-background"
  style={{
    backgroundImage: `url(${kinauraSplashBg})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed'
  }}
>
  {/* Semi-transparent overlay for readability */}
  <div className="kinaura-app-overlay">
    {children}
  </div>
</div>
```

### Component Guidelines
- **Cards**: Semi-transparent white with backdrop blur
- **Panels**: 92% opacity with subtle blur
- **Text**: Ensure WCAG AA contrast compliance
- **Overlays**: Use ivory with 85% opacity for readability

## Platform Integration

### iOS Configuration
1. Replace icons in `ios/App/App/Assets.xcassets/AppIcon.appiconset/`
2. Update splash in `ios/App/App/Assets.xcassets/Splash.imageset/`
3. Set LaunchScreen.storyboard background to `#FAFAF7`
4. Configure status bar for dark content

### Android Configuration
1. Replace adaptive icons in `android/app/src/main/res/mipmap-*/`
2. Update splash screens in `android/app/src/main/res/drawable-*/`
3. Set background color to ivory in `ic_launcher_background.xml`
4. Configure foreground with KinAura symbol

### Web/PWA Configuration
1. Update `manifest.json` with KinAura theme colors
2. Generate favicons using `kinaura-symbol.svg`
3. Ensure maskable icon support for modern browsers

## Asset Generation Commands

### Capacitor Assets (if working)
```bash
cd frontend
npx @capacitor/assets generate
```

### Manual Update Process
1. Replace source files in `assets/brand/`
2. Copy to `public/brand/` for web access
3. Update platform-specific asset directories
4. Run `npx cap sync ios` and `npx cap sync android`
5. Test on devices for proper scaling

### PWA Assets
```bash
npx pwa-asset-generator ./assets/brand/kinaura-symbol.svg ./public \
  --padding "15%" --background "#FAFAF7" --opaque false --favicon --mstile --manifest
```

## Quality Assurance

### Visual Checklist
- [ ] App icons show KinAura symbol without text
- [ ] Splash screens use ivory background with centered symbol
- [ ] All app screens display consistent luxury background
- [ ] No distortion or cropping of symbol across sizes
- [ ] Cards and panels maintain readability over background

### Functional Checklist  
- [ ] iOS and Android builds succeed after asset updates
- [ ] Icons scale correctly from 48px to 1024px
- [ ] No layout shift from splash to first screen
- [ ] Web/PWA icons display correctly in browsers
- [ ] Background performance acceptable on all devices

### Accessibility Checklist
- [ ] Contrast meets WCAG AA standards (4.5:1 for text)
- [ ] Gold on ivory decorative elements don't interfere with content
- [ ] Splash screen duration is minimal and non-interactive
- [ ] Background doesn't cause motion sensitivity issues

## Brand Consistency

### Do's
- ✅ Use official KinAura symbol for all app icons
- ✅ Maintain ivory + gold color scheme across platforms
- ✅ Apply subtle transparency to content areas
- ✅ Ensure luxury, premium aesthetic throughout
- ✅ Follow platform-specific design guidelines

### Don'ts
- ❌ Don't add text to app launcher icons
- ❌ Don't use colors outside the approved palette
- ❌ Don't make background too prominent over content
- ❌ Don't use low-resolution or pixelated assets
- ❌ Don't ignore accessibility requirements

## Update Workflow

1. **Asset Changes**: Update source files in `assets/brand/`
2. **Generate**: Run asset generation tools
3. **Copy**: Update `public/brand/` for web access
4. **Platform Sync**: Run `npx cap sync` for mobile platforms
5. **Test**: Verify on all target devices and browsers
6. **Document**: Update this guide if process changes

## Contact & Resources

- **Design System**: `/frontend/src/styles/kinaura-theme.css`
- **Design Tokens**: `/frontend/src/designTokens.js`
- **Brand Assets**: Contact design team for source files
- **Platform Guidelines**: Apple HIG, Material Design, PWA specs