<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="scroll-smooth">

<head>
    <title>{{config('app.name', 'SINEMA')}}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Sistem Informasi Ekstrakurikuler Mahasiswa Fakultas Teknik Universitas Tadulako">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="icon" type="image/x-png" href="{{ asset('favicon.png') }}">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    @stack('styles')
</head>

<body class="bg-gray-50 text-gray-80 font-['Inter']">
    <div id="app">
        <!-- Header / Navbar -->
        @unless(request()->is('admin/*'))
            <header id="header" class="bg-white/80 backdrop-blur-md sticky top-0 z-40 shadow-sm">
                <div class="container mx-auto px-6 py-4 flex justify-between items-center">
                    <img src="{{asset('images/sinema.png')}}" alt="Logo Sinema" class="h-12 w-auto">
                    <nav class="hidden md:flex items-center space-x-8">
                        <a href="{{ url('/') }}" class="text-gray-600 hover:text-amber-500 transition-colors">Beranda</a>
                        <a href="#fitur" class="text-gray-600 hover:text-amber-500 transition-colors">Fitur</a>
                        <a href="#tentang" class="text-gray-600 hover:text-amber-500 transition-colors">Tentang</a>
                        <a href="#faq" class="text-gray-600 hover:text-amber-500 transition-colors">FAQ</a>
                    </nav>
                    @guest
                        <a href="/admin/login"
                            class="bg-amber-500 text-white font-semibold px-5 py-2 rounded-lg hover:bg-amber-600 transition-all shadow-md">
                            Masuk
                        </a>
                    @else
                        <div class="flex items-center space-x-3">
                            <span class="text-gray-600">{{ Auth::user()->name }}</span>
                            <a href="/admin"
                                class="bg-amber-500 text-white font-semibold px-5 py-2 rounded-lg hover:bg-amber-600 transition-all shadow-md">
                                Dashboard
                            </a>
                        </div>
                    @endguest
                </div>
            </header>
        @endunless

        <!-- Main Content -->
        <main class="@unless(request()->is('admin/*')) min-h-screen @endunless">
            @yield('content')
        </main>

        <!-- Footer -->
        @unless(request()->is('admin/*'))
            <footer class="bg-gray-800 text-white py-12">
                <div class="container mx-auto px-6 text-center">
                    <h3 class="text-3xl font-bold">Mulai Kumpulkan Poin Ekstrakurikuler Anda Hari Ini!</h3>
                    @guest
                        <a href="/admin/register"
                            class="mt-8 inline-block bg-amber-500 text-white font-bold px-8 py-4 rounded-lg hover:bg-amber-600 transition-all shadow-lg text-lg">
                            Daftar Sekarang
                        </a>
                    @endguest
                    <div class="mt-12 border-t border-gray-700 pt-8">
                        <p>&copy; 2025 SINEMA - Universitas Tadulako. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        @endunless
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    @stack('scripts')

    <!-- Chatbot Component - Only show on non-admin pages for guest users -->
    @guest
        @unless(request()->is('admin/*'))
            <x-chatbot />
        @endunless
    @endguest
</body>

</html>