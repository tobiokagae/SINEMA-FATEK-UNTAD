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
        Schema::create('daily_stats_chatbot', function (Blueprint $table) {
            $table->id();
            $table->date('date')->unique();
            $table->integer('total_queries')->default(0);
            $table->integer('cache_hits')->default(0);
            $table->integer('positive_feedback')->default(0);
            $table->integer('negative_feedback')->default(0);
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('daily_stats_chatbot');
    }
};
