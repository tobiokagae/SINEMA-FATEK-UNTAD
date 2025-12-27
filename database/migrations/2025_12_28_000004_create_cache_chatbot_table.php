<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('cache_chatbot', function (Blueprint $table) {
            $table->id();
            $table->string('query_hash', 64);
            $table->text('query');
            $table->text('response');
            $table->json('sources')->nullable();
            $table->float('latency')->nullable();
            $table->integer('hits')->default(0);
            $table->timestamps();

            $table->index('query_hash');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('cache_chatbot');
    }
};
