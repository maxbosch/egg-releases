import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'Egg — Put all your eggs in one basket.',description:'Screenshots, voice notes, links, photos of doors. Everything you grab, wherever you grab it, ends up on your Mac.'};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="en"><body>{children}</body></html>}
