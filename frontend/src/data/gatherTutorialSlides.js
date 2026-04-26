import {
  CalendarDays,
  Camera,
  MapPinned,
  Sparkles,
} from 'lucide-vue-next'
import faceIdAnimationUrl from '@/assets/animations/face-id.lottie?url'
import pleaseSignHereAnimationUrl from '@/assets/animations/please-sign-here.lottie?url'
import satelliteAnimationUrl from '@/assets/animations/satellite.lottie?url'
import societyAnimationUrl from '@/assets/animations/society.lottie?url'

export const gatherTutorialSlides = [
  {
    id: 'introducing-gather',
    artSize: 198,
    title: 'Introducing Gather',
    titlePrefix: 'Introducing',
    titleGradient: {
      text: 'Gather',
      colors: ['#5227FF', '#FF9FFC', '#B19EEF'],
      animationSpeed: 8,
      showBorder: false,
      direction: 'horizontal',
    },
    description: 'Forget the clipboard and the roll call. Gather instantly recognizes everyone in the room with one tap. Snap a photo and get back to what matters most—connecting with your people.',
    animationSrc: societyAnimationUrl,
    fallbackIcon: Sparkles,
    fallbackLabel: 'Gather introduction animation',
  },
  {
    id: 'share-location',
    artSize: 236,
    title: 'Share Your\nLocation',
    description: 'Allow location access so Gather can discover nearby attendance-ready events happening around you right now.',
    animationSrc: satelliteAnimationUrl,
    fallbackIcon: MapPinned,
    fallbackLabel: 'Location animation slot',
  },
  {
    id: 'choose-event',
    artSize: 236,
    title: 'Choose an\nEvent',
    description: 'Pick the active event you want to open so Gather can prepare the right attendance flow and timing window.',
    animationSrc: pleaseSignHereAnimationUrl,
    fallbackIcon: CalendarDays,
    fallbackLabel: 'Event selection animation slot',
  },
  {
    id: 'scan-faces',
    artSize: 236,
    title: 'Scan\nFaces Live',
    description: 'Open the live kiosk, arm the camera, and let Gather handle the quick face-attendance experience in real time.',
    animationSrc: faceIdAnimationUrl,
    fallbackIcon: Camera,
    fallbackLabel: 'Face scan animation slot',
  },
]
